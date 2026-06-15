"""
News fetcher: finds startup credit program announcements from last 7 days.
Uses NewsAPI (free tier) + RSS fallback.
"""
import os
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from rich.console import Console

console = Console()
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

SEARCH_QUERIES = [
    "startup credits cloud AI 2026",
    "AWS startup program credits",
    "Anthropic startup credits",
    "OpenAI startup credits",
    "Google Cloud startup program",
    "voice AI startup credits",
]

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://news.ycombinator.com/rss",
    "https://www.producthunt.com/feed",
]

KEYWORDS = [
    "startup credit", "startup program", "free credits", "aws activate",
    "anthropic startup", "openai startup", "cloud credits", "founders hub",
    "deepgram startup", "assemblyai startup", "elevenlabs grants",
    "google for startups", "nvidia inception",
]


def _is_recent(date_str: str, days: int = 7) -> bool:
    """Check if a date string is within the last N days."""
    if not date_str:
        return False
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        # Try formats from most to least specific — never slice the string
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",   # RSS: Sat, 07 Jun 2026 12:00:00 +0000
            "%a, %d %b %Y %H:%M:%S %Z",   # RSS with named tz: GMT
            "%Y-%m-%dT%H:%M:%S%z",         # ISO 8601 with tz
            "%Y-%m-%dT%H:%M:%SZ",          # ISO 8601 UTC Z
            "%Y-%m-%dT%H:%M:%S",           # ISO 8601 no tz
            "%Y-%m-%d",                    # date only
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt >= cutoff
            except ValueError:
                continue
    except Exception:
        pass
    return False


def _matches_keywords(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in KEYWORDS)


def fetch_news_api() -> list[dict]:
    if not NEWS_API_KEY:
        console.print("[yellow]NEWS_API_KEY not set — skipping NewsAPI[/yellow]")
        return []

    results = []
    base_url = "https://newsapi.org/v2/everything"
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    for query in SEARCH_QUERIES[:3]:  # limit to 3 queries on free tier
        try:
            resp = requests.get(base_url, params={
                "q": query,
                "from": seven_days_ago,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": NEWS_API_KEY,
                "pageSize": 5,
            }, timeout=10)
            if resp.status_code == 200:
                for article in resp.json().get("articles", []):
                    title = article.get("title", "")
                    if _matches_keywords(title + " " + article.get("description", "")):
                        results.append({
                            "title": title,
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "date": article.get("publishedAt", "")[:10],
                            "url": article.get("url", ""),
                            "summary": (article.get("description") or "")[:200],
                        })
        except Exception as e:
            console.print(f"[red]NewsAPI error for '{query}': {e}[/red]")

    console.print(f"[green]✓ NewsAPI: {len(results)} relevant articles[/green]")
    return results


def fetch_rss() -> list[dict]:
    results = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:200]
                pub_date = entry.get("published", "")
                link = entry.get("link", "")

                if _matches_keywords(title + " " + summary) and _is_recent(pub_date):
                    results.append({
                        "title": title,
                        "source": feed.feed.get("title", feed_url),
                        "date": pub_date[:10] if pub_date else "Unknown",
                        "url": link,
                        "summary": summary,
                    })
        except Exception as e:
            console.print(f"[red]RSS error for {feed_url}: {e}[/red]")

    console.print(f"[green]✓ RSS feeds: {len(results)} relevant items[/green]")
    return results


def fetch_all_news() -> list[dict]:
    console.print("[cyan]Fetching recent news...[/cyan]")
    items = fetch_news_api() + fetch_rss()
    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for item in items:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique.append(item)
    console.print(f"[bold green]Total unique news items: {len(unique)}[/bold green]")
    return unique
