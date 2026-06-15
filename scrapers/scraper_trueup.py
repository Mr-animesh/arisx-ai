"""
Scraper: trueup.io/build/startup-credit-programs
Clean table-based layout — easier to parse.
"""
import re
from bs4 import BeautifulSoup
from utils.http import fetch
from utils.models import CreditProgram
from rich.console import Console

console = Console()
SOURCE = "trueup.io"
URL = "https://www.trueup.io/build/startup-credit-programs"


def _guess_category(name: str, category_raw: str) -> str:
    t = (name + " " + category_raw).lower()
    if any(k in t for k in ["aws", "azure", "google cloud", "gcp", "digitalocean", "cloudflare", "ibm"]):
        return "☁️ Cloud Infra"
    if any(k in t for k in ["openai", "anthropic", "mistral", "together", "cohere", "ai platform", "llm"]):
        return "🤖 AI / LLM"
    if any(k in t for k in ["deepgram", "assemblyai", "elevenlabs", "voice", "speech"]):
        return "🎙️ Voice / STT/TTS"
    if any(k in t for k in ["nvidia", "gpu"]):
        return "🖥️ GPU / Hardware"
    if any(k in t for k in ["hubspot", "crm"]):
        return "📈 CRM / Growth"
    if any(k in t for k in ["stripe", "brex", "ramp", "mercury"]):
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

    # trueup renders a list/table of programs
    rows = soup.find_all("tr")
    if not rows:
        # fallback: find list items with dollar amounts
        rows = soup.find_all("li")

    seen = set()
    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            # Try as a list item
            text = row.get_text(separator=" ", strip=True)
            if not text or len(text) < 10:
                continue
            amounts = re.findall(r'\$[\d,]+(?:K|M)?', text)
            credit_amount = amounts[0] if amounts else "Varies"
            link = row.find("a", href=True)
            provider = text.split("·")[0].strip()[:40] if "·" in text else text[:40]
            if not provider or provider in seen:
                continue
            seen.add(provider)
            programs.append(CreditProgram(
                provider=provider,
                program_name=f"{provider} Startup Program",
                category=_guess_category(provider, text),
                credit_amount=credit_amount,
                validity="12 months",
                eligibility="Early-stage startup",
                requires_vc="No",
                apply_url=link["href"] if link and link["href"].startswith("http") else URL,
                notes=text[:200],
                source_site=SOURCE,
            ))
            continue

        # Table row parsing
        provider_cell = cells[0].get_text(strip=True)
        amount_cell = cells[1].get_text(strip=True) if len(cells) > 1 else "Varies"
        validity_cell = cells[2].get_text(strip=True) if len(cells) > 2 else "12 months"
        category_raw = cells[3].get_text(strip=True) if len(cells) > 3 else ""

        if not provider_cell or provider_cell.lower() in ["program", "provider", "name", ""]:
            continue
        if provider_cell in seen:
            continue
        seen.add(provider_cell)

        link = row.find("a", href=True)
        apply_url = link["href"] if link else URL

        programs.append(CreditProgram(
            provider=provider_cell.split("·")[0].strip(),
            program_name=f"{provider_cell.split('·')[0].strip()} Startup Program",
            category=_guess_category(provider_cell, category_raw),
            credit_amount=amount_cell,
            validity=validity_cell,
            eligibility="Early-stage startup",
            requires_vc="No",
            apply_url=apply_url if apply_url.startswith("http") else f"https://www.trueup.io{apply_url}",
            notes="",
            source_site=SOURCE,
        ))

    console.print(f"[green]✓ {SOURCE}: {len(programs)} programs found[/green]")
    return programs
