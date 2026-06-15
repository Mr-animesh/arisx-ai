# ⚡ ArisX Startup Credits Scraper

Automated scraper that aggregates **34+ startup credit programs** (AWS, Anthropic, Deepgram, OpenAI, Google Cloud, etc.) and pushes them to a Google Sheet with deduplication, a news feed, and a 24-hour scheduler.

---

## 📁 Project Structure

```
arisx-credits-scraper/
├── run.py                          # Entry point (CLI + scheduler)
├── pipeline.py                     # Core orchestrator
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── scrapers/
│   ├── scraper_seed.py             # 34 verified programs (always runs, fallback)
│   ├── scraper_creditforstartups.py
│   ├── scraper_trueup.py
│   ├── scraper_klymentiev.py
│   └── news_fetcher.py             # NewsAPI + RSS for freshness tab
│
├── sheets/
│   └── sheets_manager.py           # Auth, upsert, dedup, formatting
│
└── utils/
    ├── models.py                   # CreditProgram dataclass
    ├── http.py                     # Retry + rotating headers
    └── notifier.py                 # Optional Slack alerts
```

---

## 🚀 Quick Start (5 minutes)

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/arisx-credits-scraper
cd arisx-credits-scraper
pip install -r requirements.txt
```

### 2. Set up Google Sheets API

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable **Google Sheets API** + **Google Drive API**
3. Create a **Service Account** → Download the JSON key → save as `credentials.json` in project root
4. Create a new Google Sheet → Copy the Sheet ID from the URL
5. Share the sheet with the service account email (from the JSON file) as **Editor**

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env:
# GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
# GOOGLE_SHEET_ID=your_sheet_id_here
# NEWS_API_KEY=your_key_from_newsapi.org  (optional, free tier)
# SLACK_WEBHOOK_URL=...                   (optional)
```

### 4. Run

```bash
# Run once immediately
python run.py
# Immediately runs complete pipeline and push changes to sheets
python run.py --now
# Preview without pushing to Sheets
python run.py --dry-run
# Run on 24-hour schedule (keeps process alive)
python run.py --schedule
# Run every 6 hours
python run.py --schedule --interval 6
```
### 5. Run with Docker (optional)

```bash
# Place credentials.json in project root, configure .env
docker-compose up -d
```
### 6. Run SQLite query

```bash
#install sqlite
sudo apt install sqlite3

#example query
sqlite3 credits.db "SELECT provider, program_name, first_seen, last_updated FROM credits LIMIT 5;"
```
---

## 📊 Google Sheet Output

The script creates 3 tabs automatically:
| Tab | Contents |
|-----|----------|
| **Credits Tracker** | All programs: Provider, Program Name, Category, Credits, Validity, Eligibility, Requires VC?, Apply URL, Notes, Source |
| **Recent News** | News/posts from last 7 days about startup credit programs |
| **Run Log** | Timestamp + stats for every pipeline run |

### Deduplication Logic
- Key = `provider::program_name` (lowercased)
- If the key already exists in the sheet → **UPDATE** that row
- If new → **INSERT** at the bottom
- Guarantees the sheet stays clean across multiple daily runs

---

## 🔧 Adding a New Scraper

Create `scrapers/scraper_yoursite.py`:

```python
from utils.models import CreditProgram
from utils.http import fetch
from bs4 import BeautifulSoup

SOURCE = "yoursite.com"
URL = "https://yoursite.com/startup-credits"

def scrape() -> list[CreditProgram]:
    html = fetch(URL)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    # ... parse logic ...
    return [CreditProgram(...)]
```

Then register it in `pipeline.py`:
```python
from scrapers.scraper_yoursite import scrape as scrape_yoursite
scrapers.append(("yoursite.com", scrape_yoursite))
```
---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅ Yes | Path to service account JSON key |
| `GOOGLE_SHEET_ID` | ✅ Yes | Google Sheet ID from URL |
| `NEWS_API_KEY` | Optional | Free key from newsapi.org |
| `SLACK_WEBHOOK_URL` | Optional | Slack incoming webhook for alerts |
| `REQUEST_DELAY_SECONDS` | Optional | Delay between requests (default: 2) |
| `MAX_RETRIES` | Optional | HTTP retry count (default: 3) |

---

## 🧠 Architecture Notes

- **Seed data always runs first** — guarantees 34 verified programs even if all web scrapers fail
- **Web scrapers override seed data** — live scraper results win on dedup (last-write-wins)
- **Graceful failure** — each scraper is wrapped in try/except; one failing doesn't stop others
- **Rate limiting** — rotating User-Agent headers + configurable delay between requests
- **Scheduler** — uses `schedule` library; runs in foreground (use `nohup` or Docker for production)

---

## 📈 Estimated Credit Value

| Category | Min | Max |
|----------|-----|-----|
| ☁️ Cloud Infra | $6K | $750K |
| 🤖 AI / LLM | $8.5K | $185K |
| 🎙️ Voice / STT/TTS | $14K | $200K |
| 🛠️ Dev Tools | $2K | $200K |
| 🖥️ GPU / Hardware | $0 | $250K |
| 🏦 Fintech / Misc | $5K | $110K |
| **TOTAL** | **~$40K** | **~$1.7M** |

---

## 🏗️ Built for ArisX
Voice AI startup | Production at scale | Mumbai / Remote
