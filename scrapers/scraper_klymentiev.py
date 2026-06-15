"""
Scraper: klymentiev.com/blog/free-ai-api-credits
Long-form blog post with structured sections per provider.
"""
import re
from bs4 import BeautifulSoup
from utils.http import fetch
from utils.models import CreditProgram
from rich.console import Console

console = Console()
SOURCE = "klymentiev.com"
URL = "https://klymentiev.com/blog/free-ai-api-credits"


PROVIDER_PATTERNS = {
    "OpenAI":      ("🤖 AI / LLM", "https://openai.com/for-startups"),
    "Anthropic":   ("🤖 AI / LLM", "https://www.anthropic.com/startups"),
    "Mistral":     ("🤖 AI / LLM", "https://mistral.ai/"),
    "Together":    ("🤖 AI / LLM", "https://www.together.ai/startups"),
    "Deepgram":    ("🎙️ Voice / STT/TTS", "https://deepgram.com/startup-program"),
    "AssemblyAI":  ("🎙️ Voice / STT/TTS", "https://www.assemblyai.com/"),
    "ElevenLabs":  ("🎙️ Voice / STT/TTS", "https://elevenlabs.io/grants"),
    "Runway":      ("🤖 AI / LLM", "https://runwayml.com/"),
    "Fireworks":   ("🤖 AI / LLM", "https://fireworks.ai/"),
    "Perplexity":  ("🤖 AI / LLM", "https://www.perplexity.ai/"),
    "Cohere":      ("🤖 AI / LLM", "https://cohere.com/"),
}


def scrape() -> list[CreditProgram]:
    console.print(f"[cyan]Scraping {SOURCE}...[/cyan]")
    html = fetch(URL)
    if not html:
        console.print(f"[red]Skipping {SOURCE} — fetch failed[/red]")
        return []

    soup = BeautifulSoup(html, "lxml")
    programs = []
    seen = set()

    # Find all headings — each provider gets its own section
    headings = soup.find_all(["h2", "h3"])

    for heading in headings:
        heading_text = heading.get_text(strip=True)

        # Match known providers
        matched_provider = None
        for provider in PROVIDER_PATTERNS:
            if provider.lower() in heading_text.lower():
                matched_provider = provider
                break

        if not matched_provider or matched_provider in seen:
            continue
        seen.add(matched_provider)

        # Grab the next sibling paragraphs/lists for context
        context_parts = []
        sibling = heading.find_next_sibling()
        for _ in range(5):
            if sibling is None:
                break
            if sibling.name in ["h2", "h3"]:
                break
            context_parts.append(sibling.get_text(separator=" ", strip=True))
            sibling = sibling.find_next_sibling()
        context = " ".join(context_parts)[:400]

        # Extract credit amount from context
        amounts = re.findall(r'\$[\d,]+(?:K|M)?(?:\s*(?:–|-|to)\s*\$[\d,]+(?:K|M)?)?', context)
        credit_amount = amounts[0] if amounts else "Varies"

        # Extract validity
        validity = "12 months"
        validity_match = re.search(r'(\d+)\s*(month|year)s?', context, re.IGNORECASE)
        if validity_match:
            n, unit = validity_match.group(1), validity_match.group(2).lower()
            validity = f"{n} {'month' if 'month' in unit else 'year'}{'s' if int(n) > 1 else ''}"

        # Requires VC?
        requires_vc = "Yes" if any(k in context.lower() for k in ["vc", "backed", "venture", "accelerator required"]) else "No"

        category, apply_url = PROVIDER_PATTERNS[matched_provider]

        programs.append(CreditProgram(
            provider=matched_provider,
            program_name=f"{matched_provider} AI Startup Program",
            category=category,
            credit_amount=credit_amount,
            validity=validity,
            eligibility="AI startup; early-stage",
            requires_vc=requires_vc,
            apply_url=apply_url,
            notes=context[:200],
            source_site=SOURCE,
        ))

    console.print(f"[green]✓ {SOURCE}: {len(programs)} programs found[/green]")
    return programs
