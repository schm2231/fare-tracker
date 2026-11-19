"""Pick which trips to price today.

Every destination has PATTERNS x WEEKS_AHEAD possible trips. Each day we
price a different seeded sample of them, so over about a month the whole
space is covered and the history captures lead time and weekday effects.
"""
import datetime as dt
import random

from . import config


def candidate_trips(today: dt.date):
    for name, weekday, nights in config.PATTERNS:
        first = today + dt.timedelta(days=(weekday - today.weekday()) % 7 or 7)
        for w in range(config.WEEKS_AHEAD):
            depart = first + dt.timedelta(weeks=w)
            yield name, depart, depart + dt.timedelta(days=nights)


def trips_for(today: dt.date, dest: str, k: int | None = None):
    k = k or config.SAMPLES_PER_DEST
    pool = list(candidate_trips(today))
    rng = random.Random(f"{today.isoformat()}-{dest}")
    return sorted(rng.sample(pool, min(k, len(pool))), key=lambda t: t[1])
