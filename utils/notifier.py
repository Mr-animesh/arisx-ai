"""
Slack notifier: sends a summary message when new programs are found.
Optional — only fires if SLACK_WEBHOOK_URL is set.
"""
import os
import json
import requests
from rich.console import Console

console = Console()
WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")


def notify(new_programs: list, news_items: list):
    if not WEBHOOK:
        return

    if not new_programs and not news_items:
        return

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "⚡ ArisX Credits Tracker — New Updates"}
        },
    ]

    if new_programs:
        program_lines = "\n".join(
            f"• *{p.provider}* — {p.program_name} ({p.credit_amount})"
            for p in new_programs[:10]
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🆕 {len(new_programs)} New Programs Found:*\n{program_lines}"}
        })

    if news_items:
        news_lines = "\n".join(
            f"• <{item['url']}|{item['title'][:60]}> — _{item['source']}_"
            for item in news_items[:5]
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📰 {len(news_items)} Recent News Items:*\n{news_lines}"}
        })

    blocks.append({"type": "divider"})

    try:
        resp = requests.post(WEBHOOK, data=json.dumps({"blocks": blocks}),
                             headers={"Content-Type": "application/json"}, timeout=10)
        if resp.status_code == 200:
            console.print("[green]✓ Slack notification sent[/green]")
        else:
            console.print(f"[yellow]Slack returned {resp.status_code}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Slack notify failed: {e}[/yellow]")
