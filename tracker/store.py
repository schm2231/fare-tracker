"""Append-only fare history, one CSV per month under data/fares/."""
import csv
import pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "fares"
FIELDS = [
    "observed", "source", "origin", "dest", "pattern", "depart", "return",
    "nights", "lead_days", "price_usd", "airlines", "stops", "duration_min",
]


def append(rows: list[dict], month: str) -> pathlib.Path:
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / f"{month}.csv"
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)
    return path


def load_all() -> list[dict]:
    rows = []
    for p in sorted(DATA.glob("*.csv")):
        with p.open() as f:
            rows.extend(csv.DictReader(f))
    return rows
