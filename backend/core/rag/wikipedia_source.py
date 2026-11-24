import httpx
import ssl
from utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": "TrustLLMSystem/1.0 (educational FYP project)"
}

WIKIPEDIA_SEARCH = "https://en.wikipedia.org/w/api.php"


async def search_wikipedia(query: str, max_results: int = 3) -> list[str]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": max_results,
    }
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, verify=ssl.create_default_context()) as client:
            response = await client.get(WIKIPEDIA_SEARCH, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("query", {}).get("search", [])
            return [r["title"] for r in results]
    except Exception as exc:
        logger.error("wikipedia_search_failed", error=str(exc))
        return []


async def fetch_wikipedia_content(title: str) -> str:
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=15, headers=HEADERS, verify=ssl.create_default_context()) as client:
            response = await client.get(WIKIPEDIA_SEARCH, params=params)
            response.raise_for_status()
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                return page.get("extract", "")
        return ""
    except Exception as exc:
        logger.error("wikipedia_fetch_failed", title=title, error=str(exc))
        return ""


async def fetch_rag_context(query: str) -> tuple[list[str], list[str]]:
    titles = await search_wikipedia(query, max_results=3)
    contents = []
    sources = []

    for title in titles:
        content = await fetch_wikipedia_content(title)
        if content:
            contents.append(content)
            sources.append(f"Wikipedia: {title}")

    logger.info("rag_context_fetched", sources=sources)
    return contents, sources