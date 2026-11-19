# fare-tracker

Free, self-building flight fare history from MSP.

Every morning a GitHub Actions job prices a rotating sample of round trips
(weekend and week-long shapes, up to 26 weeks out) to 50 destinations in the
US, Canada, Europe and South America, and appends them to `data/fares/YYYY-MM.csv`.
Over time this answers: which departure/return days are cheapest, how far
ahead to book, which months are cheap, and whether today's fare is a deal.

- **Page:** https://schm2231.github.io/fare-tracker/
- **Google Sheet:** `=IMPORTDATA("https://raw.githubusercontent.com/schm2231/fare-tracker/main/docs/latest.csv")` (also `deals.csv`, `patterns.csv`)
- **Email:** set repo secrets `GMAIL_USER`, `GMAIL_APP_PASSWORD` (Gmail app password), optional `EMAIL_TO` (comma-separated).
- **Watchlist:** add destination codes to `watchlist.txt`. Watched routes are starred and listed first.
- Edit destinations and trip shapes in `tracker/config.py`.
- Run by hand: Actions tab → "Daily fare log" → Run workflow (set a limit like 10 for a quick test).
- Local: `pip install -r requirements.txt && python -m tracker.run --limit 5`

Data sources: the free Travelpayouts Data API (secret `TRAVELPAYOUTS_TOKEN`, main source)
plus a small Google Flights sample via the unofficial `fast-flights` scraper, which is
mostly blocked from GitHub runners. A red run means nothing was priced, so check the log.

## Local run (Jon's PC)

Google blocks most requests from GitHub, so `local_run.ps1` scrapes the 25
international destinations from a home connection every evening (Windows Task
Scheduler, task "MSP fare tracker"), writes `data/fares/YYYY-MM-local.csv`
and pushes it. The next morning's GitHub run folds it into the page, Sheet
and email. Log: `local_run.log`.
