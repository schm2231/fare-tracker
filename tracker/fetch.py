"""Price one round trip using the free fast-flights Google Flights scraper."""
from dataclasses import dataclass
import datetime as dt

from fast_flights import FlightQuery, Passengers, create_query, get_flights


@dataclass
class Quote:
    price_usd: int
    airlines: str
    stops: int
    duration_min: int


def cheapest(origin: str, dest: str, depart: dt.date, ret: dt.date) -> Quote | None:
    q = create_query(
        flights=[
            FlightQuery(date=depart.isoformat(), from_airport=origin, to_airport=dest),
            FlightQuery(date=ret.isoformat(), from_airport=dest, to_airport=origin),
        ],
        seat="economy",
        trip="round-trip",
        passengers=Passengers(adults=1),
        currency="USD",
    )
    results = [r for r in get_flights(q) if r.price and r.price > 0]
    if not results:
        return None
    best = min(results, key=lambda r: r.price)
    return Quote(
        price_usd=int(best.price),
        airlines="/".join(best.airlines),
        stops=max(len(best.flights) - 1, 0),
        duration_min=sum(f.duration for f in best.flights),
    )
