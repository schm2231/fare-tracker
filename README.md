# fare-tracker

Free, self-building flight fare history from MSP.

Every morning a GitHub Actions job prices a rotating sample of round trips
(weekend and week-long shapes, up to 26 weeks out) to 50 destinations in the
US, Canada, Europe and South America, and appends them to `data/fares/YYYY-MM.csv`.
Over time this answers: which departure/return days are cheapest, how far
ahead to book, which months are cheap, and whether today's fare is a deal.

- Edit destinations and trip shapes in `tracker/config.py`.
- Run by hand: Actions tab → "Daily fare log" → Run workflow (set a limit like 10 for a quick test).
- Local: `pip install -r requirements.txt && python -m tracker.run --limit 5`

Data source: Google Flights via the open-source `fast-flights` scraper. It's
free and unofficial, so it can break or be blocked. A red run means check the log.
