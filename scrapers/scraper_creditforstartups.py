"""
Scraper: creditforstartups.com/credits
Parses the credit cards listing page.
"""
from bs4 import BeautifulSoup
from utils.http import fetch
from utils.models import CreditProgram
from rich.console import Console

console = Console()
SOURCE = "creditforstartups.com"
URL = "https://creditforstartups.com/credits"


def _guess_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["aws", "azure", "google cloud", "gcp", "digital ocean", "cloudflare", "ibm", "oracle"]):
        return "☁️ Cloud Infra"
    if any(k in t for k in ["openai", "anthropic", "mistral", "together", "cohere", "llm", "gpt"]):
        return "🤖 AI / LLM"
    if any(k in t for k in ["deepgram", "assemblyai", "elevenlabs", "voice", "speech", "sarvam"]):
        return "🎙️ Voice / STT/TTS"
    if any(k in t for k in ["nvidia", "gpu", "h100"]):
        return "🖥️ GPU / Hardware"
    if any(k in t for k in ["hubspot", "crm", "salesforce", "marketing"]):
        return "📈 CRM / Growth"
    if any(k in t for k in ["stripe", "brex", "ramp", "mercury", "fintech"]):
        return "🏦 Fintech / Misc"
    return "🛠️ Dev Tools"


def scrape() -> list[CreditProgram]:
    console.print(f"[cyan]Scraping {SOURCE}...[/cyan]")
    html = fetch(URL)
    if not html:
        console.print(f"[red]Skipping {SOURCE} — fetch failed[/red]")
        return []

    soup = BeautifulSoup(html, "lxml")
    programs = []

    # The site renders credit cards — look for card-like containers
    cards = soup.find_all(["article", "div"], class_=lambda c: c and any(
        k in c for k in ["card", "credit", "perk", "program", "item"]
    ))

    # Fallback: find all anchor tags that look like program links
    if not cards:
        cards = soup.select("a[href*='/credits/'], a[href*='/companies/']")

    seen = set()
    for card in cards:
        text = card.get_text(separator=" ", strip=True)
        if len(text) < 20:
            continue

        # Extract provider name (usually first bold/heading element)
        heading = card.find(["h2", "h3", "h4", "strong", "b"])
        provider = heading.get_text(strip=True) if heading else "Unknown"
        if not provider or provider in seen:
            continue
        seen.add(provider)

        # Extract credit amount — look for $ patterns
        import re
        amounts = re.findall(r'\$[\d,]+(?:K|M)?(?:\s*(?:–|-|to)\s*\$[\d,]+(?:K|M)?)?', text)
        credit_amount = amounts[0] if amounts else "Varies"

        # Extract apply link
        link_tag = card.find("a", href=True)
        apply_url = link_tag["href"] if link_tag else URL

        programs.append(CreditProgram(
            provider=provider,
            program_name=f"{provider} Startup Credits",
            category=_guess_category(text),
            credit_amount=credit_amount,
            validity="12 months",
            eligibility="Early-stage startup",
            requires_vc="No",
            apply_url=apply_url if apply_url.startswith("http") else f"https://creditforstartups.com{apply_url}",
            notes=text[:200],
            source_site=SOURCE,
        ))

    console.print(f"[green]✓ {SOURCE}: {len(programs)} programs found[/green]")
    return programs
