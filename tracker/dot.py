"""US DOT Consumer Airfare Report (Table 1a, airport pairs), MSP routes only.

Quarterly average fares back to 1993 give an immediate "which time of year
is cheapest" baseline for US routes, long before our own logs can.
Writes data/dot_baseline.csv. Run quarterly (DOT publishes ~6 months late).
"""
import csv
import json
import pathlib
import urllib.parse
import urllib.request

from . import config

URL = "https://data.transportation.gov/resource/tfrh-tu9e.json"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "dot_baseline.csv"


def main():
    rows, offset = [], 0
    while True:
        q = {
            "$select": "year,quarter,airport_1,airport_2,passengers,fare,fare_low,carrier_low",
            "$where": f"airport_1='{config.ORIGIN}' OR airport_2='{config.ORIGIN}'",
            "$order": "tbl1apk", "$limit": 50000, "$offset": offset,
        }
        with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=120) as r:
            page = json.load(r)
        rows += page
        if len(page) < 50000:
            break
        offset += 50000
    out = []
    for r in rows:
        other = r["airport_2"] if r["airport_1"] == config.ORIGIN else r["airport_1"]
        if other in config.DOMESTIC and r.get("fare"):
            out.append({"year": r["year"], "quarter": r["quarter"], "dest": other,
                        "fare": r["fare"], "fare_low": r.get("fare_low", ""),
                        "carrier_low": r.get("carrier_low", ""), "passengers": r.get("passengers", "")})
    out.sort(key=lambda x: (x["dest"], int(x["year"]), int(x["quarter"])))
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    yrs = sorted({int(x["year"]) for x in out})
    print(f"dot: {len(rows)} MSP rows, kept {len(out)} for {len({x['dest'] for x in out})} destinations, {yrs[0]}-{yrs[-1]}")


if __name__ == "__main__":
    main()
