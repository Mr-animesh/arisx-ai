"""
ArisX Startup Credits Scraper
Entry point with CLI flags + 24-hour scheduler.

Usage:
    python run.py --now          # Run once immediately
    python run.py --dry-run      # Run without pushing to Sheets
    python run.py --schedule     # Run on 24h schedule (blocks)
    python run.py --serve        # Scheduler (background) + FastAPI server
    python run.py                # Default: run once (same as --now)
"""
import argparse
import schedule
import threading
import time
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="ArisX Startup Credits Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                  # Run once immediately
  python run.py --dry-run        # Preview without pushing to Sheets
  python run.py --schedule       # Run every 24 hours (keep process alive)
  python run.py --schedule --interval 6  # Run every 6 hours
  python run.py --serve          # Scheduler + API server together
  python run.py --serve --port 8080      # Custom API port
        """
    )
    parser.add_argument("--now", action="store_true", help="Run pipeline once immediately")
    parser.add_argument("--dry-run", action="store_true", help="Run without pushing to Sheets")
    parser.add_argument("--json", action="store_true", help="Output results as JSON (implies --dry-run)")
    parser.add_argument("--schedule", action="store_true", help="Run on a recurring schedule")
    parser.add_argument("--serve", action="store_true", help="Run scheduler + FastAPI server together")
    parser.add_argument("--interval", type=int, default=24, help="Schedule interval in hours (default: 24)")
    parser.add_argument("--port", type=int, default=8000, help="API server port for --serve (default: 8000)")
    args = parser.parse_args()

    if args.json:
        args.dry_run = True

    # Import here to allow .env to load first
    from pipeline import run_pipeline

    def job():
        try:
            run_pipeline(dry_run=args.dry_run, json_output=args.json)
        except Exception as e:
            console.print(f"[bold red]Pipeline error: {e}[/bold red]")
            import traceback
            traceback.print_exc()

    if args.serve:
        console.print(
            f"[bold cyan]Starting API server on port {args.port} "
            f"+ scheduler every {args.interval}h[/bold cyan]"
        )
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        def scheduler_loop():
            job()
            schedule.every(args.interval).hours.do(job)
            while True:
                schedule.run_pending()
                time.sleep(60)

        threading.Thread(target=scheduler_loop, daemon=True).start()

        import uvicorn
        from api.server import app

        uvicorn.run(app, host="0.0.0.0", port=args.port)
    elif args.schedule:
        console.print(f"[bold cyan]Scheduler started — running every {args.interval} hours[/bold cyan]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        # Run immediately first, then on schedule
        job()
        schedule.every(args.interval).hours.do(job)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            console.print("\n[yellow]Scheduler stopped.[/yellow]")
    else:
        # Default: run once
        job()


if __name__ == "__main__":
    main()
