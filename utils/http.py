import time
import random
import os
import requests
from typing import Optional
from rich.console import Console

console = Console()

HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    },
]

DELAY = float(os.getenv("REQUEST_DELAY_SECONDS", "2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))


def fetch(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch URL with retry + rotating headers. Returns HTML text or None."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = random.choice(HEADERS_POOL)
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                time.sleep(DELAY + random.uniform(0, 1))
                return resp.text
            elif resp.status_code == 429:
                wait = 10 * attempt
                console.print(f"[yellow]Rate limited on {url}. Waiting {wait}s...[/yellow]")
                time.sleep(wait)
            else:
                console.print(f"[red]HTTP {resp.status_code} on {url} (attempt {attempt})[/red]")
        except requests.RequestException as e:
            console.print(f"[red]Request error on {url}: {e} (attempt {attempt})[/red]")
            time.sleep(3 * attempt)
    console.print(f"[bold red]Failed to fetch {url} after {MAX_RETRIES} attempts[/bold red]")
    return None
