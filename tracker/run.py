"""Daily logger: price a sample of trips from MSP and append them to history.

Usage: python -m tracker.run [--limit N] [--dest DEN,LHR]
"""
import argparse
import datetime as dt
import random
import sys
import time

from . import config, fetch, sampler, store


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="stop after N requests (smoke test)")
    ap.add_argument("--dest", help="comma-separated destinations to override the list")
    args = ap.parse_args(argv)

    today = dt.date.today()
    dests = args.dest.split(",") if args.dest else config.DESTINATIONS
    rows, ok, empty, failed, done = [], 0, 0, 0, 0

    for dest in dests:
        for pattern, depart, ret in sampler.trips_for(today, dest):
            if args.limit and done >= args.limit:
                break
            done += 1
            try:
                q = fetch.cheapest(config.ORIGIN, dest, depart, ret)
            except Exception as e:  # network, parse, or block
                failed += 1
                print(f"FAIL {dest} {depart} {type(e).__name__}: {str(e)[:150]}", file=sys.stderr)
                q = None
            else:
                if q is None:
                    empty += 1
            if q:
                ok += 1
                rows.append({
                    "observed": today.isoformat(), "origin": config.ORIGIN, "dest": dest,
                    "pattern": pattern, "depart": depart.isoformat(), "return": ret.isoformat(),
                    "nights": (ret - depart).days, "lead_days": (depart - today).days,
                    "price_usd": q.price_usd, "airlines": q.airlines, "stops": q.stops,
                    "duration_min": q.duration_min,
                })
                print(f"ok   {dest} {pattern} {depart} ${q.price_usd}")
            time.sleep(random.uniform(*config.DELAY_SECONDS))

    if rows:
        path = store.append(rows, today.strftime("%Y-%m"))
        print(f"wrote {len(rows)} rows to {path}")
    print(f"summary: {done} requests, {ok} priced, {empty} no results, {failed} failed")
    # Google flakes on many requests, so only go red when nothing at all was priced.
    return 1 if done and ok == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
