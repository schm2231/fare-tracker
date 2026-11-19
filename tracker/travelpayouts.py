"""Cached round-trip fares from the free Travelpayouts (Aviasales) Data API.

Prices come from recent real searches by Aviasales users, so popular
routes are well covered. Needs TRAVELPAYOUTS_TOKEN in the environment.
"""
import datetime as dt
import json
import os
import time
import urllib.parse
import urllib.request

from . import config

URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"


def classify(depart: dt.date, ret: dt.date) -> str:
    nights = (ret - depart).days
    for name, weekday, n in config.PATTERNS:
        if depart.weekday() == weekday and nights == n:
            return name
    kind = "wknd" if nights <= 4 else "week"
    return f"{kind}-{depart.strftime('%a').lower()}-{nights}n"


def _get(params: dict, token: str) -> list[dict]:
    req = urllib.request.Request(
        URL + "?" + urllib.parse.urlencode(params),
        headers={"X-Access-Token": token, "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if not body.get("success", True):
        raise RuntimeError(body.get("error") or "api error")
    return body.get("data") or []


def collect(today: dt.date, dests: list[str], token: str | None = None) -> tuple[list[dict], int]:
    token = token or os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        return [], 0
    rows, failed = [], 0
    months = sorted({(today + dt.timedelta(days=30 * i)).strftime("%Y-%m") for i in range(7)})
    for dest in dests:
        best: dict[tuple, dict] = {}
        for month in months:
            try:
                data = _get({
                    "origin": config.ORIGIN, "destination": dest, "departure_at": month,
                    "one_way": "false", "currency": "usd", "market": "us",
                    "sorting": "price", "limit": 1000,
                }, token)
            except Exception as e:
                failed += 1
                print(f"FAIL tp {dest} {month} {type(e).__name__}: {str(e)[:150]}")
                continue
            for d in data:
                if not d.get("return_at") or not d.get("price"):
                    continue
                dep = dt.date.fromisoformat(d["departure_at"][:10])
                ret = dt.date.fromisoformat(d["return_at"][:10])
                nights = (ret - dep).days
                if dep <= today or not (2 <= nights <= 9):
                    continue
                key = (dep, ret)
                if key in best and best[key]["price_usd"] <= d["price"]:
                    continue
                best[key] = {
                    "observed": today.isoformat(), "source": "travelpayouts",
                    "origin": config.ORIGIN, "dest": dest, "pattern": classify(dep, ret),
                    "depart": dep.isoformat(), "return": ret.isoformat(), "nights": nights,
                    "lead_days": (dep - today).days, "price_usd": int(d["price"]),
                    "airlines": d.get("airline", ""),
                    "stops": max(d.get("transfers", 0) or 0, d.get("return_transfers", 0) or 0),
                    "duration_min": d.get("duration_to") or "",
                }
            time.sleep(0.3)
        rows.extend(best.values())
        print(f"tp   {dest}: {len(best)} trips")
    return rows, failed
