"""
Core pipeline: runs all scrapers, deduplicates, pushes to Google Sheets.
"""

import dataclasses
import json
from rich.console import Console
from rich.table import Table

from scrapers.scraper_seed import scrape as scrape_seed
from scrapers.scraper_creditforstartups import scrape as scrape_creditforstartups
from scrapers.scraper_trueup import scrape as scrape_trueup
from scrapers.scraper_klymentiev import scrape as scrape_klymentiev
from scrapers.scraper_startupcredits import scrape as scrape_startupcredits
from scrapers.scraper_guptadeepak import scrape as scrape_guptadeepak
from scrapers.news_fetcher import fetch_all_news
from sheets.sheets_manager import push_programs, push_news, log_run
from db.database import get_all_programs, upsert_programs
from utils.models import CreditProgram
from utils.notifier import notify

console = Console()


def run_pipeline(dry_run: bool = False, json_output: bool = False) -> dict:
    import sys

    if json_output:
        sys.stdout = sys.stderr
    console.rule("[bold cyan]⚡ ArisX Credits Scraper — Starting Pipeline[/bold cyan]")

    # ── 1. Run all scrapers ──────────────────────────────────────────────────
    all_programs: list[CreditProgram] = []

    # Seed data always runs first (guaranteed baseline)
    all_programs += scrape_seed()

    # Live scrapers (may fail gracefully)
    scrapers = [
        ("creditforstartups.com", scrape_creditforstartups),
        ("trueup.io", scrape_trueup),
        ("klymentiev.com", scrape_klymentiev),
        ("startupcredits.dev", scrape_startupcredits),
        ("guptadeepak.com", scrape_guptadeepak),
        # TODO add scraper name
    ]

    for name, scrape_fn in scrapers:
        try:
            results = scrape_fn()
            all_programs += results
        except Exception as e:
            console.print(f"[red]Scraper '{name}' crashed: {e}[/red]")

    # ── 2. Persist to SQLite (INSERT new, UPDATE existing) ─────────────────
    inserted, updated = upsert_programs(all_programs)
    unique_programs = get_all_programs()
    console.print(
        f"\n[bold]DB: {inserted} inserted, {updated} updated — "
        f"{len(unique_programs)} total programs[/bold]"
    )

    # ── 3. Print summary table ───────────────────────────────────────────────
    table = Table(title="Programs Found", show_lines=True)
    table.add_column("Provider", style="cyan", width=18)
    table.add_column("Program", width=28)
    table.add_column("Category", width=20)
    table.add_column("Credits", style="green", width=18)
    table.add_column("VC?", width=6)

    for p in sorted(unique_programs, key=lambda x: x.category):
        table.add_row(
            p.provider,
            p.program_name[:28],
            p.category,
            p.credit_amount[:18],
            p.requires_vc,
        )
    console.print(table)

    # ── 4. Fetch news ────────────────────────────────────────────────────────
    news_items = fetch_all_news()

    # ── 5. Push to Google Sheets (unless dry run) ────────────────────────────
    if json_output:
        output = {
            "programs": [dataclasses.asdict(p) for p in unique_programs],
            "news": [dataclasses.asdict(n) for n in news_items],
            "total_programs": len(unique_programs),
            "total_news": len(news_items),
        }
        sys.__stdout__.write(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    elif dry_run:
        console.print("\n[yellow]DRY RUN — skipping Google Sheets push[/yellow]")
        console.print(
            f"Would push {len(unique_programs)} programs + {len(news_items)} news items"
        )
    else:
        push_programs(unique_programs)
        push_news(news_items)
        log_run(len(unique_programs), inserted, updated, len(news_items))

    # ── 6. Slack notification ────────────────────────────────────────────────
    if not dry_run:
        notify(unique_programs[:5], news_items[:3])

    console.rule("[bold green]✓ Pipeline Complete[/bold green]")
    return {
        "total_programs": len(unique_programs),
        "news_items": len(news_items),
    }
