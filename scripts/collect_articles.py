"""
Collects articles from free trusted sources.
Run once to build your knowledge base.
"""
import httpx
import json
import os
from pathlib import Path

HEADERS = {
    "User-Agent": "TrustLLMSystem/1.0 (educational FYP project)"
}

# Topics to fetch from Wikipedia
WIKIPEDIA_TOPICS = [
    # Physics & Science
    "Speed of light",
    "Quantum mechanics",
    "Theory of relativity",
    "Photon",
    "Electromagnetic radiation",

    # Indian Politics
    "Siddaramaiah",
    "Droupadi Murmu",
    "Narendra Modi",
    "Karnataka",
    "Chief Minister of Karnataka",
    "Indian general election 2024",
    "Bharatiya Janata Party",
    "Indian National Congress",
    "M. K. Stalin",
    "Tamil Nadu",
    "Chief Minister of Tamil Nadu",
    "Dravida Munnetra Kazhagam",
    "Vijay (actor)",
    "Tamilaga Vettri Kazhagam",

    # World Politics
    "Donald Trump",
    "Joe Biden",
    "2024 United States presidential election",
    "Elon Musk",
    "Twitter",

    # Sports
    "2025 Indian Premier League",
    "Royal Challengers Bengaluru",
    "Virat Kohli",
    "Pluto",
    "Solar System",

    # Technology & AI
    "Artificial intelligence",
    "Large language model",
    "ChatGPT",
    "OpenAI",
    "Anthropic",
    "Machine learning",
    "Deep learning",
]

OUTPUT_DIR = Path("data/knowledge_base")


def fetch_wikipedia_article(title: str) -> dict:
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "format": "json",
    }
    try:
        r = httpx.get(
            "https://en.wikipedia.org/w/api.php",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            if extract and len(extract) > 100:
                return {
                    "title": title,
                    "content": extract,
                    "source": f"Wikipedia: {title}",
                    "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                }
    except Exception as e:
        print(f"Failed to fetch {title}: {e}")
    return {}


def collect_all_articles():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    articles = []

    print(f"Collecting {len(WIKIPEDIA_TOPICS)} articles...")

    for i, topic in enumerate(WIKIPEDIA_TOPICS):
        print(f"[{i+1}/{len(WIKIPEDIA_TOPICS)}] Fetching: {topic}")
        article = fetch_wikipedia_article(topic)
        if article:
            articles.append(article)
            print(f"  ✓ Got {len(article['content'])} chars")
        else:
            print(f"  ✗ Failed")

    output_file = OUTPUT_DIR / "articles.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(articles)} articles to {output_file}")
    return articles


if __name__ == "__main__":
    collect_all_articles()
