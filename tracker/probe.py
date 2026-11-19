"""Diagnostic: compare success rates of query shapes against Google Flights."""
import datetime as dt, time, random, collections
from fast_flights import FlightQuery, Passengers, create_query, get_flights
from . import sampler

stats = collections.Counter()
today = dt.date.today()
trips = [(d, t) for d in ["DEN", "ORD", "LHR", "YYZ"] for t in sampler.trips_for(today, d, 4)]
for dest, (_, dep, ret) in trips:
    variants = {
        "rt-en": dict(trip="round-trip", language="en-US", legs=[(dep, "MSP", dest), (ret, dest, "MSP")]),
        "rt-blank": dict(trip="round-trip", language="", legs=[(dep, "MSP", dest), (ret, dest, "MSP")]),
        "ow-out": dict(trip="one-way", language="en-US", legs=[(dep, "MSP", dest)]),
        "ow-back": dict(trip="one-way", language="en-US", legs=[(ret, dest, "MSP")]),
    }
    for name, v in variants.items():
        q = create_query(flights=[FlightQuery(date=d.isoformat(), from_airport=a, to_airport=b) for d, a, b in v["legs"]],
                         trip=v["trip"], language=v["language"], currency="USD", passengers=Passengers(adults=1))
        try:
            r = get_flights(q); p = min(x.price for x in r if x.price)
            stats[name + " ok"] += 1; print(name, dest, dep, "ok", p, flush=True)
        except Exception as e:
            stats[name + " fail"] += 1; print(name, dest, dep, "FAIL", type(e).__name__, flush=True)
        time.sleep(random.uniform(1.5, 3))
print(dict(sorted(stats.items())))
