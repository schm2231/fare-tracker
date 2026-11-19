"""What to track. Edit these lists to change the destinations."""

ORIGIN = "MSP"

# 25 busiest domestic destinations from MSP (approximate)
DOMESTIC = [
    "DEN", "ORD", "PHX", "LAS", "ATL", "DFW", "LAX", "MCO", "SEA", "SFO",
    "LGA", "BOS", "DCA", "FLL", "TPA", "RSW", "SAN", "AUS", "IAH", "MIA",
    "SLC", "PDX", "BNA", "MSY", "HNL",
]

# 25 international: Canada, Europe, South America
INTERNATIONAL = [
    # Canada
    "YYZ", "YVR", "YUL", "YWG", "YYC",
    # Europe
    "LHR", "CDG", "AMS", "FRA", "KEF", "DUB", "FCO", "BCN", "MAD", "LIS",
    "MUC", "ZRH", "ATH", "CPH", "ARN",
    # South America
    "BOG", "LIM", "GRU", "EZE", "SCL",
]

DESTINATIONS = DOMESTIC + INTERNATIONAL

# Trip shapes: (name, depart weekday Mon=0, nights)
# Several weekend and week-long variants, so the data shows which
# departure and return days are cheapest.
PATTERNS = [
    ("wknd-thu-sun", 3, 3),
    ("wknd-fri-sun", 4, 2),
    ("wknd-fri-mon", 4, 3),
    ("wknd-sat-mon", 5, 2),
    ("week-sat-sat", 5, 7),
    ("week-sun-sun", 6, 7),
    ("week-tue-tue", 1, 7),
    ("week-wed-wed", 2, 7),
]

WEEKS_AHEAD = 26          # look about 6 months out
SAMPLES_PER_DEST = 6      # default sample size
GOOGLE_SAMPLES_PER_DEST = 2  # Google is flaky from GitHub, keep this small
DELAY_SECONDS = (2.0, 4.0)  # polite random pause between requests

CITY = {
    "DEN": "Denver", "ORD": "Chicago", "PHX": "Phoenix", "LAS": "Las Vegas", "ATL": "Atlanta",
    "DFW": "Dallas", "LAX": "Los Angeles", "MCO": "Orlando", "SEA": "Seattle", "SFO": "San Francisco",
    "LGA": "New York", "BOS": "Boston", "DCA": "Washington DC", "FLL": "Fort Lauderdale",
    "TPA": "Tampa", "RSW": "Fort Myers", "SAN": "San Diego", "AUS": "Austin", "IAH": "Houston",
    "MIA": "Miami", "SLC": "Salt Lake City", "PDX": "Portland", "BNA": "Nashville",
    "MSY": "New Orleans", "HNL": "Honolulu",
    "YYZ": "Toronto", "YVR": "Vancouver", "YUL": "Montreal", "YWG": "Winnipeg", "YYC": "Calgary",
    "LHR": "London", "CDG": "Paris", "AMS": "Amsterdam", "FRA": "Frankfurt", "KEF": "Reykjavik",
    "DUB": "Dublin", "FCO": "Rome", "BCN": "Barcelona", "MAD": "Madrid", "LIS": "Lisbon",
    "MUC": "Munich", "ZRH": "Zurich", "ATH": "Athens", "CPH": "Copenhagen", "ARN": "Stockholm",
    "BOG": "Bogota", "LIM": "Lima", "GRU": "Sao Paulo", "EZE": "Buenos Aires", "SCL": "Santiago",
}

REGION = {**{d: "USA" for d in DOMESTIC},
          **{d: "Canada" for d in ["YYZ", "YVR", "YUL", "YWG", "YYC"]},
          **{d: "South America" for d in ["BOG", "LIM", "GRU", "EZE", "SCL"]}}
for _d in INTERNATIONAL:
    REGION.setdefault(_d, "Europe")

# Alerts: a fare counts as a deal when it is this far below the route's
# typical (median) daily-cheapest price, once there's enough history.
DEAL_THRESHOLD = 0.80     # 20% or more below typical
MIN_HISTORY_DAYS = 7
