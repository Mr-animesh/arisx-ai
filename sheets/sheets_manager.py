"""
Google Sheets manager.
Handles: auth, header setup, dedup upsert, news tab push.
"""

import os
import gspread
from google.oauth2.service_account import Credentials
from utils.models import CreditProgram, SHEET_HEADERS, NEWS_HEADERS
from rich.console import Console

console = Console()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

MAIN_TAB = "Credits Tracker"
NEWS_TAB = "Recent News"
LOG_TAB = "Run Log"


def _get_client() -> gspread.Client:
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_or_create_sheet(
    spreadsheet: gspread.Spreadsheet, title: str
) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=20)
        return ws


def _ensure_headers(ws: gspread.Worksheet, headers: list[str]):
    existing = ws.row_values(1)
    if existing != headers:
        ws.update("A1", [headers])
        # Bold the header row (formatting via Sheets API)
        try:
            ws.format(
                "A1:Z1",
                {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.12, "green": 0.14, "blue": 0.20},
                },
            )
        except Exception:
            pass


def _build_dedup_map(ws: gspread.Worksheet) -> dict[str, int]:
    """Returns {provider::program_name -> row_number} for existing rows."""
    all_values = ws.get_all_values()
    dedup_map = {}
    for i, row in enumerate(all_values[1:], start=2):  # skip header
        if len(row) >= 2:
            key = f"{row[0].lower().strip()}::{row[1].lower().strip()}"
            dedup_map[key] = i
    return dedup_map


def push_programs(programs: list[CreditProgram]):
    """Upsert all programs into the Credits Tracker tab."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        console.print("[bold red]GOOGLE_SHEET_ID not set in .env[/bold red]")
        return
    console.print("[cyan]Connecting to Google Sheets...[/cyan]")
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    ws = _get_or_create_sheet(spreadsheet, MAIN_TAB)
    _ensure_headers(ws, SHEET_HEADERS)
    existing_map = _build_dedup_map(ws)
    new_rows = []
    updated = 0
    for program in programs:
        key = program.dedup_key
        row_data = program.to_row()
        if key in existing_map:
            # UPDATE existing row
            row_num = existing_map[key]
            ws.update(f"A{row_num}", [row_data])
            updated += 1
        else:
            # QUEUE for batch insert
            new_rows.append(row_data)
            existing_map[key] = -1  # mark as handled to avoid dupes in same batch
    # Batch append new rows
    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")
    console.print(
        f"[bold green]✓ Sheets: {len(new_rows)} new rows inserted, {updated} updated[/bold green]"
    )
    _apply_conditional_formatting(ws)


def push_news(news_items: list[dict]):
    """Push news items to the Recent News tab."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id or not news_items:
        return
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    ws = _get_or_create_sheet(spreadsheet, NEWS_TAB)
    _ensure_headers(ws, NEWS_HEADERS)
    existing_urls = set()
    for row in ws.get_all_values()[1:]:
        if len(row) >= 4:
            existing_urls.add(row[3])  # URL is column 4
    new_rows = []
    for item in news_items:
        if item["url"] not in existing_urls:
            new_rows.append(
                [
                    item["title"],
                    item["source"],
                    item["date"],
                    item["url"],
                    item["summary"],
                ]
            )
            existing_urls.add(item["url"])
    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")
        console.print(
            f"[bold green]✓ News tab: {len(new_rows)} new items added[/bold green]"
        )
    else:
        console.print("[yellow]News tab: no new items to add[/yellow]")


def log_run(total_programs: int, new_count: int, updated_count: int, news_count: int):
    """Append a run summary row to the Log tab."""
    from datetime import datetime

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        return
    try:
        client = _get_client()
        spreadsheet = client.open_by_key(sheet_id)
        ws = _get_or_create_sheet(spreadsheet, LOG_TAB)
        _ensure_headers(
            ws,
            ["Timestamp", "Total Programs", "New Rows", "Updated Rows", "News Items"],
        )
        ws.append_rows(
            [
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    total_programs,
                    new_count,
                    updated_count,
                    news_count,
                ]
            ]
        )
    except Exception as e:
        console.print(f"[yellow]Log write failed: {e}[/yellow]")


def _apply_conditional_formatting(ws: gspread.Worksheet):
    """Apply basic color formatting to category column."""
    try:
        # Color the header row
        ws.format(
            "A1:J1",
            {
                "textFormat": {
                    "bold": True,
                    "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                },
                "backgroundColor": {"red": 0.12, "green": 0.14, "blue": 0.20},
            },
        )
    except Exception:
        pass  # Formatting is optional
