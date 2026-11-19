import json, os, urllib.request, urllib.parse, datetime as dt
T=os.environ["TRAVELPAYOUTS_TOKEN"]
def get(url, p):
    req=urllib.request.Request(url+"?"+urllib.parse.urlencode(p),headers={"X-Access-Token":T})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: b=json.load(r)
    except Exception as e: return f"ERR {e}"
    d=b.get("data"); return len(d) if isinstance(d,(list,dict)) else d
months=[(dt.date.today()+dt.timedelta(days=30*i)).strftime("%Y-%m") for i in range(1,4)]
for air,city in [("LHR","LON"),("CDG","PAR"),("YYZ","YTO"),("LGA","NYC"),("GRU","SAO"),("SEA","SEA"),("KEF","REK")]:
    for dest in (air,city):
        for market in ("us",None):
            n=0; m2=0
            for m in months:
                p={"origin":"MSP","destination":dest,"departure_at":m,"one_way":"false","currency":"usd","sorting":"price","limit":1000}
                if market: p["market"]=market
                r=get("https://api.travelpayouts.com/aviasales/v3/prices_for_dates",p); n+= r if isinstance(r,int) else 0
                p2={"origin":"MSP","destination":dest,"group_by":"departure_at","departure_at":m,"min_trip_duration":2,"max_trip_duration":9,"currency":"usd"}
                if market: p2["market"]=market
                r2=get("https://api.travelpayouts.com/aviasales/v3/grouped_prices",p2); m2+= r2 if isinstance(r2,int) else 0
            print(dest, market, "pfd", n, "grouped", m2, flush=True)
    r=get("https://api.travelpayouts.com/v2/prices/latest",{"origin":"MSP","destination":city,"currency":"usd","period_type":"year","one_way":"false","limit":1000})
    print(city,"latest",r)
