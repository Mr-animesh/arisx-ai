"""
Scraper: guptadeepak.com/startup-offers
Curated blog listing tech software, server credits, and operations tooling discounts.
"""

import re
from bs4 import BeautifulSoup
from utils.http import fetch
from utils.models import CreditProgram
from rich.console import Console

console = Console()
SOURCE = "guptadeepak.com"
URL = "https://guptadeepak.com/startup-offers"

PROVIDER_PATTERNS = {
    "DigitalOcean": ("☁️ Cloud Infrastructure", "https://www.digitalocean.com/"),
    "Notion": ("📝 Productivity / Docs", "https://www.notion.so/startups"),
    "Brex": ("💳 Fintech / Payments", "https://www.brex.com/"),
    "Mixpanel": ("📊 Analytics / Data", "https://mixpanel.com/startups/"),
    "Segment": ("📊 Analytics / Data", "https://segment.com/industry/startups/"),
    "Intercom": (
        "💬 Customer Support",
        "https://www.intercom.com/early-stage-startups",
    ),
}


def scrape() -> list[CreditProgram]:
    console.print(f"[cyan]Scraping {SOURCE}...[/cyan]")

    # Graceful error handling: return an empty list if blocked/offline
    try:
        html = fetch(URL)
        if not html:
            console.print(f"[red]Skipping {SOURCE} — fetch failed[/red]")
            return []
    except Exception as e:
        console.print(f"[red]Skipping {SOURCE} — exception raised: {e}[/red]")
        return []

    soup = BeautifulSoup(html, "lxml")
    programs = []
    seen = set()

    # Dig into elements containing list elements, links, or headers
    blocks = soup.find_all(["li", "p", "h3", "div"])

    for block in blocks:
        block_text = block.get_text(strip=True)

        matched_provider = None
        for provider in PROVIDER_PATTERNS:
            if provider.lower() in block_text.lower():
                matched_provider = provider
                break

        if not matched_provider or matched_provider in seen:
            continue
        seen.add(matched_provider)

        context = block_text[:400]

        # Extract credit financial amount formatting expressions
        amounts = re.findall(
            r"\$[\d,]+(?:K|M)?(?:\s*(?:–|-|to)\s*\$[\d,]+(?:K|M)?)?|\d+%\s*off",
            context,
            re.IGNORECASE,
        )
        credit_amount = amounts[0] if amounts else "Varies / Discount"

        validity = "12 months"
        validity_match = re.search(r"(\d+)\s*(month|year)s?", context, re.IGNORECASE)
        if validity_match:
            n, unit = validity_match.group(1), validity_match.group(2).lower()
            validity = f"{n} {'month' if 'month' in unit else 'year'}{'s' if int(n) > 1 else ''}"

        requires_vc = (
            "Yes"
            if any(k in context.lower() for k in ["vc", "backed", "accelerator"])
            else "No"
        )
        category, apply_url = PROVIDER_PATTERNS[matched_provider]

        programs.append(
            CreditProgram(
                provider=matched_provider,
                program_name=f"{matched_provider} Startup Offer",
                category=category,
                credit_amount=credit_amount,
                validity=validity,
                eligibility="Verified startup applicant",
                requires_vc=requires_vc,
                apply_url=apply_url,
                notes=context[:200],
                source_site=SOURCE,
            )
        )

    console.print(f"[green]✓ {SOURCE}: {len(programs)} programs found[/green]")
    return programs
