"""Turn the fare history into docs/data.json, docs/latest.csv and docs/deals.csv.

docs/ is served by GitHub Pages; the Google Sheet imports the CSVs.
"""
import csv
import datetime as dt
import json
import pathlib
import statistics as st
from collections import defaultdict

from . import config, store

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
LEAD_BUCKETS = [(0, 14, "< 2 wks"), (14, 30, "2-4 wks"), (30, 60, "1-2 mo"),
                (60, 90, "2-3 mo"), (90, 120, "3-4 mo"), (120, 999, "4+ mo")]


def kind_of(row) -> str:
    return "wknd" if int(row["nights"]) <= 4 else "week"


def load_watchlist() -> list[tuple[str, str | None]]:
    p = ROOT / "watchlist.txt"
    out = []
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                parts = line.upper().split()
                out.append((parts[0], parts[1].lower() if len(parts) > 1 else None))
    return out


def is_watched(dest, kind, wl) -> bool:
    return any(d == dest and (k is None or k == kind) for d, k in wl)


def build() -> dict:
    # Same trip logged twice on one day (e.g. a manual re-run): keep the cheapest.
    uniq = {}
    for r in store.load_all():
        if not r.get("price_usd"):
            continue
        r["price_usd"] = int(r["price_usd"])
        r["kind"] = kind_of(r)
        k = (r["observed"], r["dest"], r["depart"], r["return"])
        if k not in uniq or r["price_usd"] < uniq[k]["price_usd"]:
            uniq[k] = r
    rows = list(uniq.values())
    if not rows:
        return {"generated": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%MZ"), "n_rows": 0}

    days = sorted({r["observed"] for r in rows})
    latest = days[-1]
    wl = load_watchlist()

    # Daily cheapest per route+kind: the series alerts are judged against.
    daily_min: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        k = (r["dest"], r["kind"])
        cur = daily_min[k].get(r["observed"])
        if cur is None or r["price_usd"] < cur["price_usd"]:
            daily_min[k][r["observed"]] = r

    # Typical price per route+kind across all observations, for pattern indexes.
    route_median = {}
    by_route = defaultdict(list)
    for r in rows:
        by_route[(r["dest"], r["kind"])].append(r["price_usd"])
    for k, v in by_route.items():
        route_median[k] = st.median(v)

    dot = dot_quarter_avg()

    cheapest, deals = [], []
    for (dest, kind), series in daily_min.items():
        today = series.get(latest)
        if not today:
            continue
        past = [s["price_usd"] for d, s in series.items() if d != latest]
        typical = st.median(past) if past else None
        pct = round(100 * (today["price_usd"] / typical - 1)) if typical else None
        item = {
            "dest": dest, "city": config.CITY.get(dest, dest), "region": config.REGION.get(dest, ""),
            "kind": kind, "price": today["price_usd"], "depart": today["depart"],
            "return": today["return"], "nights": int(today["nights"]),
            "depart_day": WEEKDAYS[dt.date.fromisoformat(today["depart"]).weekday()],
            "airlines": today["airlines"], "stops": int(today["stops"] or 0),
            "typical": round(typical) if typical else None, "pct_vs_typical": pct,
            "history_days": len(past), "watched": is_watched(dest, kind, wl),
        }
        # What people paid on this route in the departure's quarter (DOT, US routes only).
        b = dot.get((dest, (dt.date.fromisoformat(today["depart"]).month - 1) // 3 + 1))
        item["dot_avg"] = b["avg_rt"] if b else None
        item["dot_low"] = b["low_rt"] if b else None
        item["pct_vs_dot"] = round(100 * (today["price_usd"] / b["avg_rt"] - 1)) if b else None
        cheapest.append(item)
        if (typical and len(past) >= config.MIN_HISTORY_DAYS
                and today["price_usd"] <= typical * config.DEAL_THRESHOLD):
            deals.append(item)
    cheapest.sort(key=lambda x: (not x["watched"], x["price"]))
    deals.sort(key=lambda x: (not x["watched"], x["pct_vs_typical"]))

    # Pattern indexes: each fare relative to its route's typical price,
    # so cheap and expensive routes can be averaged together fairly.
    def index(keyfn, order=None):
        acc = defaultdict(list)
        for r in rows:
            m = route_median[(r["dest"], r["kind"])]
            if m:
                acc[keyfn(r)].append(r["price_usd"] / m)
        keys = order or sorted(acc)
        return [{"label": k, "pct": round(100 * (st.mean(acc[k]) - 1)), "n": len(acc[k])}
                for k in keys if k in acc]

    dep = lambda r: dt.date.fromisoformat(r["depart"])

    def lead_label(r):
        ld = int(r["lead_days"])
        return next(lbl for lo, hi, lbl in LEAD_BUCKETS if lo <= ld < hi)

    patterns = {
        "depart_day": index(lambda r: WEEKDAYS[dep(r).weekday()], WEEKDAYS),
        "return_day": index(lambda r: WEEKDAYS[dt.date.fromisoformat(r["return"]).weekday()], WEEKDAYS),
        "lead_time": index(lead_label, [b[2] for b in LEAD_BUCKETS]),
        "travel_month": index(lambda r: dep(r).strftime("%Y-%m")),
    }

    history = defaultdict(lambda: defaultdict(dict))
    for (dest, kind), series in daily_min.items():
        for d, s in series.items():
            history[dest][d][kind] = s["price_usd"]
    history = {dest: [{"date": d, **v} for d, v in sorted(h.items())] for dest, h in history.items()}

    return {
        "generated": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%MZ"),
        "latest": latest, "n_rows": len(rows), "n_days": len(days),
        "min_history_days": config.MIN_HISTORY_DAYS,
        "deal_threshold_pct": round(100 * (config.DEAL_THRESHOLD - 1)),
        "cheapest": cheapest, "deals": deals, "patterns": patterns, "history": history,
        "seasonal": dot_seasonal(),
    }


def dot_quarter_avg(years: int = 3, since: int = 2022) -> dict[tuple[str, int], dict]:
    """(dest, quarter) -> passenger-weighted DOT round-trip fares for that quarter,
    over its most recent `years` years (2022 on, to skip pandemic fares)."""
    p = ROOT / "data" / "dot_baseline.csv"
    if not p.exists():
        return {}
    by = defaultdict(list)
    for r in csv.DictReader(p.open()):
        if int(r["year"]) >= since and r["fare"]:
            by[(r["dest"], int(r["quarter"]))].append(r)
    out = {}
    for k, rs in by.items():
        rs = sorted(rs, key=lambda r: int(r["year"]))[-years:]
        w = [float(r["passengers"] or 1) for r in rs]
        tot = sum(w)
        avg = sum(float(r["fare"]) * x for r, x in zip(rs, w)) / tot
        low = sum(float(r["fare_low"] or r["fare"]) * x for r, x in zip(rs, w)) / tot
        out[k] = {"avg_rt": round(2 * avg), "low_rt": round(2 * low)}
    return out


def dot_seasonal() -> list[dict]:
    """Quarter-of-year price index per US route from DOT data (2015+, minus 2020-21)."""
    p = ROOT / "data" / "dot_baseline.csv"
    if not p.exists():
        return []
    by = defaultdict(lambda: defaultdict(dict))
    for r in csv.DictReader(p.open()):
        y = int(r["year"])
        if y >= 2015 and y not in (2020, 2021):
            by[r["dest"]][y][int(r["quarter"])] = float(r["fare"])
    out = []
    for dest, years in by.items():
        ratios = defaultdict(list)
        for y, qs in years.items():
            if len(qs) < 3:
                continue
            m = st.mean(qs.values())
            for q, f in qs.items():
                ratios[q].append(f / m)
        if len(ratios) < 4:
            continue
        pct = {f"Q{q}": round(100 * (st.mean(ratios[q]) - 1)) for q in range(1, 5)}
        recent = sorted((y, q, f) for y, qs in years.items() for q, f in qs.items())[-4:]
        out.append({
            "dest": dest, "city": config.CITY.get(dest, dest), **pct,
            "cheapest": min(pct, key=pct.get), "priciest": max(pct, key=pct.get),
            "recent_rt": round(2 * st.mean(f for _, _, f in recent)),
            "years": len([y for y in years if len(years[y]) >= 3]),
        })
    return sorted(out, key=lambda x: x["city"])


SHEET_FIELDS = ["watched", "city", "dest", "region", "kind", "price", "typical", "pct_vs_typical",
                "depart_day", "depart", "return", "nights", "airlines", "stops", "history_days",
                "dot_avg", "pct_vs_dot", "dot_low"]


def write(data: dict) -> None:
    DOCS.mkdir(exist_ok=True)
    (DOCS / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    for name, items in [("latest.csv", data.get("cheapest", [])), ("deals.csv", data.get("deals", []))]:
        with (DOCS / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SHEET_FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(items)
    names = {"Q1": "Jan-Mar", "Q2": "Apr-Jun", "Q3": "Jul-Sep", "Q4": "Oct-Dec"}
    with (DOCS / "seasonal.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["city", "dest", "Jan-Mar", "Apr-Jun", "Jul-Sep", "Oct-Dec", "cheapest", "typical_round_trip", "years"])
        for x in data.get("seasonal", []):
            w.writerow([x["city"], x["dest"], x["Q1"], x["Q2"], x["Q3"], x["Q4"], names[x["cheapest"]], x["recent_rt"], x["years"]])
    with (DOCS / "patterns.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pattern", "label", "pct_vs_typical", "fares"])
        for pname, items in data.get("patterns", {}).items():
            for it in items:
                w.writerow([pname, it["label"], it["pct"], it["n"]])


if __name__ == "__main__":
    d = build()
    write(d)
    print(f"report: {d.get('n_rows', 0)} rows, {len(d.get('cheapest', []))} routes, {len(d.get('deals', []))} deals")
