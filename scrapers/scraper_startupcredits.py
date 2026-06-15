"""
Scraper: startupcredits.dev
Aggregated index page listing multiple SaaS and Cloud platforms.
"""

import re
from bs4 import BeautifulSoup
from utils.http import fetch
from utils.models import CreditProgram
from rich.console import Console

console = Console()
SOURCE = "startupcredits.dev"
URL = "https://startupcredits.dev"

# Shared domain categorizations to standardize the database structure
PROVIDER_PATTERNS = {
    "AWS": ("☁️ Cloud Infrastructure", "https://aws.amazon.com/startups/"),
    "Google Cloud": ("☁️ Cloud Infrastructure", "https://cloud.google.com/startup"),
    "Stripe": (
        "💳 Fintech / Payments",
        "https://stripe.com/partners/apps-and-extensions",
    ),
    "HubSpot": ("📈 CRM / Sales", "https://www.hubspot.com/startups"),
    "OpenAI": ("🤖 AI / LLM", "https://openai.com/for-startups"),
    "Anthropic": ("🤖 AI / LLM", "https://www.anthropic.com/startups"),
    "Deel": ("👥 HR / Payroll", "https://www.deel.com/"),
}


def scrape() -> list[CreditProgram]:
    console.print(f"[cyan]Scraping {SOURCE}...[/cyan]")
    # Graceful error handling: if the fetch returns None, return an empty list
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

    # Find elements containing text cards or table rows (looking generally at links and dividers)
    cards = soup.find_all(["div", "tr", "article"])

    for card in cards:
        card_text = card.get_text(separator=" ", strip=True)
        if not card_text:
            continue

        # Match known target providers
        matched_provider = None
        for provider in PROVIDER_PATTERNS:
            if provider.lower() in card_text.lower():
                matched_provider = provider
                break

        if not matched_provider or matched_provider in seen:
            continue
        seen.add(matched_provider)

        # Context slice for localized regex scanning
        context = card_text[:400]

        # Extract credit financial amount value via Regex matching numbers with $, K, or M tags
        amounts = re.findall(
            r"\$[\d,]+(?:K|M)?(?:\s*(?:–|-|to)\s*\$[\d,]+(?:K|M)?)?", context
        )
        credit_amount = amounts[0] if amounts else "Varies"

        # Set default duration or attempt detection
        validity = "12 months"
        validity_match = re.search(r"(\d+)\s*(month|year)s?", context, re.IGNORECASE)
        if validity_match:
            n, unit = validity_match.group(1), validity_match.group(2).lower()
            validity = f"{n} {'month' if 'month' in unit else 'year'}{'s' if int(n) > 1 else ''}"

        requires_vc = (
            "Yes"
            if any(
                k in context.lower() for k in ["vc", "backed", "venture", "accelerator"]
            )
            else "No"
        )
        category, apply_url = PROVIDER_PATTERNS[matched_provider]

        programs.append(
            CreditProgram(
                provider=matched_provider,
                program_name=f"{matched_provider} Program",
                category=category,
                credit_amount=credit_amount,
                validity=validity,
                eligibility="Early-stage startup",
                requires_vc=requires_vc,
                apply_url=apply_url,
                notes=context[:200],
                source_site=SOURCE,
            )
        )

    console.print(f"[green]✓ {SOURCE}: {len(programs)} programs found[/green]")
    return programs
