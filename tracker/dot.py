"""US DOT Consumer Airfare Report (Table 6, city-pair markets), MSP routes only.

Quarterly average fares back to 1996 give an immediate "which time of year
is cheapest" baseline for US routes, long before our own logs can.

Table 6 covers every lower-48 city-pair market with at least 10 passengers a
day. Markets are metro areas: New York covers LGA, JFK and EWR, Miami covers
MIA and FLL. (Table 1a, by airport pair, only lists some MSP routes.)
Honolulu isn't in it, nor are the international routes.

DOT fares are one-way; a round trip counts as two one-way trips.
Writes data/dot_baseline.csv. Run quarterly (DOT publishes ~6 months late).
"""
import csv
import json
import pathlib
import urllib.parse
import urllib.request

from . import config

URL = "https://data.transportation.gov/resource/yj5y-b2ir.json"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "dot_baseline.csv"

ORIGIN_MARKET = "31650"  # Minneapolis/St. Paul, MN
# Destination airport -> DOT city market id
MARKET = {
    "DEN": "30325", "ORD": "30977", "PHX": "30466", "LAS": "32211", "ATL": "30397",
    "DFW": "30194", "LAX": "32575", "MCO": "31454", "SEA": "30559", "SFO": "32457",
    "LGA": "31703", "BOS": "30721", "DCA": "30852", "FLL": "32467", "TPA": "33195",
    "RSW": "31714", "SAN": "33570", "AUS": "30423", "IAH": "31453", "MIA": "32467",
    "SLC": "34614", "PDX": "34057", "BNA": "30693", "MSY": "33495",
}


def main():
    o, ids = ORIGIN_MARKET, ",".join(f"'{m}'" for m in sorted(set(MARKET.values())))
    rows, offset = [], 0
    while True:
        q = {
            "$select": "year,quarter,citymarketid_1,citymarketid_2,passengers,fare,fare_low,carrier_low",
            "$where": f"(citymarketid_1='{o}' AND citymarketid_2 in ({ids})) "
                      f"OR (citymarketid_2='{o}' AND citymarketid_1 in ({ids}))",
            "$order": "tbl6pk", "$limit": 50000, "$offset": offset,
        }
        req = urllib.request.Request(URL + "?" + urllib.parse.urlencode(q),
                                     headers={"User-Agent": "fare-tracker"})
        with urllib.request.urlopen(req, timeout=120) as r:
            page = json.load(r)
        rows += page
        if len(page) < 50000:
            break
        offset += 50000
    out = []
    for r in rows:
        market = r["citymarketid_2"] if r["citymarketid_1"] == o else r["citymarketid_1"]
        if not r.get("fare"):
            continue
        for dest in (d for d, m in MARKET.items() if m == market):
            out.append({"year": r["year"], "quarter": r["quarter"], "dest": dest,
                        "fare": r["fare"], "fare_low": r.get("fare_low", ""),
                        "carrier_low": r.get("carrier_low", ""), "passengers": r.get("passengers", "")})
    if not out:
        raise SystemExit("dot: DOT returned no MSP rows; keeping the existing file")
    out.sort(key=lambda x: (x["dest"], int(x["year"]), int(x["quarter"])))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    yrs = sorted({int(x["year"]) for x in out})
    missing = sorted(set(config.DOMESTIC) - {x["dest"] for x in out})
    print(f"dot: {len(rows)} MSP rows, kept {len(out)} for {len({x['dest'] for x in out})} destinations, "
          f"{yrs[0]}-{yrs[-1]}" + (f"; none for {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
