# Kurátorský seznam destinací pro režim „Kamkoliv" (dosažitelné z PRG/VIE/BRQ).
# region: "mesto" = city break, "plaz" = pláž, "dalka" = dálková trasa
# Víkendový režim používá jen city breaky (viz WEEKEND_DESTINATIONS).

DESTINATIONS = [
    # City breaky
    {"iata": "LHR", "city": "Londýn",     "country": "Velká Británie", "region": "mesto"},
    {"iata": "CDG", "city": "Paříž",      "country": "Francie",        "region": "mesto"},
    {"iata": "AMS", "city": "Amsterdam",  "country": "Nizozemsko",     "region": "mesto"},
    {"iata": "BRU", "city": "Brusel",     "country": "Belgie",         "region": "mesto"},
    {"iata": "CPH", "city": "Kodaň",      "country": "Dánsko",         "region": "mesto"},
    {"iata": "ARN", "city": "Stockholm",  "country": "Švédsko",        "region": "mesto"},
    {"iata": "OSL", "city": "Oslo",       "country": "Norsko",         "region": "mesto"},
    {"iata": "HEL", "city": "Helsinky",   "country": "Finsko",         "region": "mesto"},
    {"iata": "DUB", "city": "Dublin",     "country": "Irsko",          "region": "mesto"},
    {"iata": "EDI", "city": "Edinburgh",  "country": "Skotsko",        "region": "mesto"},
    {"iata": "BER", "city": "Berlín",     "country": "Německo",        "region": "mesto"},
    {"iata": "HAM", "city": "Hamburk",    "country": "Německo",        "region": "mesto"},
    {"iata": "ZRH", "city": "Curych",     "country": "Švýcarsko",      "region": "mesto"},
    {"iata": "MAD", "city": "Madrid",     "country": "Španělsko",      "region": "mesto"},
    {"iata": "BCN", "city": "Barcelona",  "country": "Španělsko",      "region": "mesto"},
    {"iata": "FCO", "city": "Řím",        "country": "Itálie",         "region": "mesto"},
    {"iata": "MXP", "city": "Milán",      "country": "Itálie",         "region": "mesto"},
    {"iata": "NAP", "city": "Neapol",     "country": "Itálie",         "region": "mesto"},
    {"iata": "LIS", "city": "Lisabon",    "country": "Portugalsko",    "region": "mesto"},
    {"iata": "OPO", "city": "Porto",      "country": "Portugalsko",    "region": "mesto"},
    {"iata": "ATH", "city": "Athény",     "country": "Řecko",          "region": "mesto"},
    {"iata": "IST", "city": "Istanbul",   "country": "Turecko",        "region": "mesto"},
    {"iata": "BUD", "city": "Budapešť",   "country": "Maďarsko",       "region": "mesto"},
    {"iata": "KRK", "city": "Krakov",     "country": "Polsko",         "region": "mesto"},
    {"iata": "DBV", "city": "Dubrovník",  "country": "Chorvatsko",     "region": "mesto"},
    {"iata": "SPU", "city": "Split",      "country": "Chorvatsko",     "region": "mesto"},

    # Pláže
    {"iata": "PMI", "city": "Palma de Mallorca", "country": "Španělsko",   "region": "plaz"},
    {"iata": "AGP", "city": "Málaga",            "country": "Španělsko",   "region": "plaz"},
    {"iata": "ALC", "city": "Alicante",          "country": "Španělsko",   "region": "plaz"},
    {"iata": "TFS", "city": "Tenerife",          "country": "Španělsko",   "region": "plaz"},
    {"iata": "LPA", "city": "Gran Canaria",      "country": "Španělsko",   "region": "plaz"},
    {"iata": "FAO", "city": "Faro",              "country": "Portugalsko", "region": "plaz"},
    {"iata": "HER", "city": "Heraklion",         "country": "Řecko",       "region": "plaz"},
    {"iata": "RHO", "city": "Rhodos",            "country": "Řecko",       "region": "plaz"},
    {"iata": "CTA", "city": "Katánie",           "country": "Itálie",      "region": "plaz"},
    {"iata": "MLA", "city": "Malta",             "country": "Malta",       "region": "plaz"},

    # Dálky — „velké dealy"
    {"iata": "JFK", "city": "New York",  "country": "USA",              "region": "dalka"},
    {"iata": "BKK", "city": "Bangkok",   "country": "Thajsko",          "region": "dalka"},
    {"iata": "DXB", "city": "Dubaj",     "country": "SAE",              "region": "dalka"},
    {"iata": "RAK", "city": "Marrákeš",  "country": "Maroko",           "region": "dalka"},
    {"iata": "MRU", "city": "Mauricius", "country": "Mauricius",        "region": "dalka"},
    {"iata": "NRT", "city": "Tokio",     "country": "Japonsko",         "region": "dalka"},
    {"iata": "SIN", "city": "Singapur",  "country": "Singapur",         "region": "dalka"},
    {"iata": "CUN", "city": "Cancún",    "country": "Mexiko",           "region": "dalka"},
]

# Víkend: jen city breaky (krátké lety, smysluplné na 2–3 noci)
WEEKEND_DESTINATIONS = [d for d in DESTINATIONS if d["region"] == "mesto"]

BY_IATA = {d["iata"]: d for d in DESTINATIONS}
