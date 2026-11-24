import asyncio
import ipaddress
import re
import socket
import ssl
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from core.rag.wikipedia_source import search_wikipedia, fetch_wikipedia_content
from models.response import EvidenceSource
from core.rag.embedder import embed_texts

HEADERS = {"User-Agent": "TrustFusion/1.0 (research evidence retrieval)"}
SOURCE_TIMEOUT_SECONDS = 18.0


def claim_search_terms(query: str, claims: list[str]) -> list[str]:
    candidates = list(dict.fromkeys(claim for claim in claims if 5 <= len(claim.split()) <= 35))
    if not candidates:
        return []
    vectors = embed_texts([query] + candidates)
    selected = []
    for candidate_idx in (vectors[1:] @ vectors[0]).argsort()[::-1]:
        vector = vectors[candidate_idx + 1]
        if float(vector @ vectors[0]) < 0.35:
            continue
        if any(float(vector @ vectors[previous + 1]) >= 0.80 for previous in selected):
            continue
        selected.append(int(candidate_idx))
        if len(selected) == 2:
            break
    return [" ".join(candidates[index].split()[:18]) for index in selected]


def extract_topics(query: str, claims: list[str] | None = None) -> list[str]:
    topic = re.split(r"[?!]|\n", query.strip(), maxsplit=1)[0]
    topic = re.sub(r"^(please\s+)?(explain|describe|what is|what are|who is|who are|tell me about)\s+",
                   "", topic, flags=re.I)
    topic = re.sub(r"^(?:the\s+)?(?:current\s+|latest\s+)?", "", topic, flags=re.I)
    topic = re.split(r"\s+(?:and describe|and explain|with examples|including)\b", topic,
                     maxsplit=1, flags=re.I)[0].strip(" .?!")
    topics = [topic or query]
    for claim in (claims or [])[:6]:
        entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", claim)
        for entity in entities:
            if entity.lower() in query.lower() and entity.lower() not in topic.lower():
                topics.append(entity)
    return list(dict.fromkeys(topics))[:3]


def public_url(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        return False
    if parsed.port not in {None, 80, 443}:
        return False
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
        return bool(addresses) and all(ipaddress.ip_address(item[4][0]).is_global
                                       for item in addresses)
    except (OSError, ValueError):
        return False


async def fetch_article(client: httpx.AsyncClient, url: str, title: str) -> EvidenceSource | None:
    try:
        for _ in range(4):
            if not await asyncio.to_thread(public_url, url):
                return None
            async with client.stream("GET", url) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers.get("location", ""))
                    continue
                response.raise_for_status()
                if "text/html" not in response.headers.get("content-type", ""):
                    return None
                body = bytearray()
                async for block in response.aiter_bytes():
                    body.extend(block)
                    if len(body) > 2_000_000:
                        return None
            soup = BeautifulSoup(bytes(body), "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            article = soup.find("article") or soup.find("main") or soup
            text = " ".join(part.get_text(" ", strip=True) for part in article.find_all("p"))
            if len(text.split()) < 50:
                return None
            return EvidenceSource(title=soup.title.get_text(strip=True) if soup.title else title,
                                  url=url, provider="web", text=text[:60000])
    except (httpx.HTTPError, ValueError, OSError):
        return None
    return None


async def fetch_dynamic_sources(query: str, claims: list[str] | None = None
                                ) -> tuple[list[EvidenceSource], list[str]]:
    topics = extract_topics(query, claims)
    claim_terms = await asyncio.to_thread(claim_search_terms, query, claims or [])
    warnings = []
    sources = []

    async def wikipedia(topic):
        titles = await search_wikipedia(topic, max_results=3)
        contents = await asyncio.gather(*(fetch_wikipedia_content(title) for title in titles))
        from urllib.parse import quote
        return [EvidenceSource(title=title,
                               url="https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_")),
                               provider="wikipedia", text=text[:100000])
                for title, text in zip(titles, contents) if text]

    async def web(topic, client):
        try:
            response = await client.get("https://html.duckduckgo.com/html/", params={"q": topic})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            links = []
            for anchor in soup.select("a.result__a"):
                url = urljoin(str(response.url), anchor.get("href", ""))
                url = parse_qs(urlsplit(url).query).get("uddg", [url])[0]
                if urlsplit(url).hostname not in {"en.wikipedia.org", "duckduckgo.com"}:
                    links.append((unquote(url), anchor.get_text(" ", strip=True)))
            results = await asyncio.gather(*(fetch_article(client, url, title)
                                             for url, title in links[:4]))
            return [result for result in results if result]
        except (httpx.HTTPError, ValueError):
            return []

    async with httpx.AsyncClient(timeout=8, headers=HEADERS, follow_redirects=False,
                                 verify=ssl.create_default_context()) as client:
        tasks = [asyncio.create_task(wikipedia(topic)) for topic in topics]
        tasks.extend(asyncio.create_task(web(topic, client))
                     for topic in list(dict.fromkeys(topics + claim_terms)))
        try:
            done, pending = await asyncio.wait(tasks, timeout=SOURCE_TIMEOUT_SECONDS)
            results = await asyncio.gather(*done, return_exceptions=True)
            if pending:
                warnings.append(f"Some evidence sources exceeded {SOURCE_TIMEOUT_SECONDS:g}s; completed sources were retained.")
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, list):
            sources.extend(result)
    sources = list({source.url: source for source in sources}.values())
    for provider in ["wikipedia", "web"]:
        if not any(source.provider == provider for source in sources):
            warnings.append(f"No live {provider} articles were available; no cached fallback was used.")
    return sources, warnings