# Obálky nad knihovnou fli (Google Flights) + syntetická data pro DEMO režim.
# DEMO režim: FLIGHT_RADAR_DEMO=1 -> žádná síť, deterministická náhodná data.
import os
import random
import time
import traceback
from datetime import date, datetime, timedelta

DEMO = os.environ.get("FLIGHT_RADAR_DEMO") == "1"

if not DEMO:
    # PyPI balík "flights", importuje se jako "fli"
    from fli.core.builders import build_date_search_segments
    from fli.models import (DateSearchFilters, FlightSearchFilters, FlightSegment,
                            PassengerInfo, SeatType, MaxStops, SortBy, TripType,
                            Airport)
    from fli.search import SearchDates, SearchFlights


# ---------------------------------------------------------------- reálný režim

def search_dates(origins: list[str], dest: str, nights: int, window_days: int,
                 max_stops: str, cfg: dict) -> list[dict]:
    """Nejlevnější cena pro každé datum v okně (round-trip). Jeden request na
    KAŽDÉ domácí letiště zvlášť — kombinovaný dotaz (více letišť najednou)
    vrací od Googlu jen zlomek cenové mřížky (ověřeno: 3 vs. 31 dat).
    Vrací [{origin, out, ret, price, currency}, ...]."""
    if DEMO:
        return _demo_dates(origins, dest, nights, window_days, cfg)

    start = date.today() + timedelta(days=2)
    end = start + timedelta(days=window_days)
    out = []

    for i, origin in enumerate(origins):
        if i:
            time.sleep(cfg.get("request_delay_seconds", 1.8))
        try:
            segments, trip_type = build_date_search_segments(
                origin=Airport[origin],
                destination=Airport[dest],
                start_date=start.isoformat(),
                trip_duration=nights,
                is_round_trip=True,
            )
            filters = DateSearchFilters(
                trip_type=trip_type,
                passenger_info=PassengerInfo(adults=cfg.get("adults", 1)),
                flight_segments=segments,
                stops=MaxStops[max_stops],
                seat_type=SeatType.ECONOMY,
                from_date=start.isoformat(),
                to_date=end.isoformat(),
                duration=nights,  # jen pro round-trip
            )
            results = SearchDates().search(
                filters,
                currency=cfg.get("currency", "CZK"),
                language=cfg.get("language", "cs"),
                country=cfg.get("country", "CZ"),
            )
        except Exception:
            traceback.print_exc()
            continue  # jedno spadlé letiště nesmí shodit celou trasu
        for dp in results or []:
            dates = dp.date if isinstance(dp.date, (tuple, list)) else (dp.date,)
            out.append({
                "origin": origin,
                "out": dates[0].date().isoformat(),
                "ret": dates[1].date().isoformat() if len(dates) > 1 else None,
                "price": float(dp.price),
                "currency": dp.currency or cfg.get("currency", "CZK"),
            })
    return out


def route_detail(origins: list[str], dest: str, out_date: str, ret_date: str,
                 max_stops: str, cfg: dict) -> list[dict]:
    """Detail letů (spoje, časy, přestupy) pro konkrétní datum. Top 3, nejlevnější první."""
    if DEMO:
        return _demo_detail(origins, dest, out_date, ret_date, cfg)

    dep = [[Airport[o], 0] for o in origins]
    arr = [[Airport[dest], 0]]
    segments = [
        FlightSegment(departure_airport=dep, arrival_airport=arr, travel_date=out_date),
        FlightSegment(departure_airport=arr[:], arrival_airport=dep[:], travel_date=ret_date),
    ]
    filters = FlightSearchFilters(
        trip_type=TripType.ROUND_TRIP,
        passenger_info=PassengerInfo(adults=cfg.get("adults", 1)),
        flight_segments=segments,
        stops=MaxStops[max_stops],
        seat_type=SeatType.ECONOMY,
        sort_by=SortBy.CHEAPEST,
    )
    results = SearchFlights().search(
        filters, top_n=3,
        currency=cfg.get("currency", "CZK"),
        language=cfg.get("language", "cs"),
        country=cfg.get("country", "CZ"),
    )
    options = []
    for item in results or []:
        try:
            # round-trip může vracet tuple (tam, zpět); cena bývá celková u druhého prvku
            if isinstance(item, tuple):
                flights = [_flight_dict(fr) for fr in item]
                price = flights[-1]["price"] or flights[0]["price"]
            else:
                flights = [_flight_dict(item)]
                price = flights[0]["price"]
            options.append({"price": price,
                            "currency": flights[0]["currency"] or cfg.get("currency", "CZK"),
                            "flights": flights})
        except Exception:
            continue  # jeden rozbitý výsledek nesmí shodit detail
    options.sort(key=lambda o: o["price"] or 0)
    return options[:3]  # Google vrací všechny kombinace tam×zpět, stačí 3 nejlevnější


def _enum_name(v):
    return getattr(v, "name", None) or str(v)


def _flight_dict(fr) -> dict:
    return {
        "price": float(fr.price) if fr.price is not None else None,
        "currency": fr.currency,
        "duration": fr.duration,       # minuty
        "stops": fr.stops,
        "airline": fr.primary_airline_name or _enum_name(fr.primary_airline),
        "legs": [{
            "airline": _enum_name(l.airline),
            "flight_number": l.flight_number,
            "from": _enum_name(l.departure_airport),
            "to": _enum_name(l.arrival_airport),
            "dep": l.departure_datetime.isoformat() if l.departure_datetime else None,
            "arr": l.arrival_datetime.isoformat() if l.arrival_datetime else None,
            "duration": l.duration,
        } for l in (fr.legs or [])],
    }


# ------------------------------------------------------------------ DEMO režim

# základní hladiny cen pro dálkové trasy; evropské se odvodí z hashe
_DEMO_LONGHAUL = {"JFK": 9800, "BKK": 13800, "DXB": 8600, "RAK": 4300,
                  "MRU": 16500, "NRT": 15800, "SIN": 14200, "CUN": 13400}
_DEMO_AIRLINES = ["Ryanair", "Wizz Air", "easyJet", "Vueling", "Austrian",
                  "Lufthansa", "KLM", "LOT", "Smartwings", "Transavia"]


def _demo_base(dest: str) -> float:
    if dest in _DEMO_LONGHAUL:
        return _DEMO_LONGHAUL[dest]
    rnd = random.Random(dest)
    return rnd.uniform(1500, 4600)


def _demo_dates(origins, dest, nights, window_days, cfg) -> list[dict]:
    base = _demo_base(dest)
    rnd = random.Random(f"{dest}:{nights}")
    start = date.today() + timedelta(days=2)
    out = []
    for i in range(window_days):
        d = start + timedelta(days=i)
        k = 0.8 + rnd.random() * 0.55
        if d.weekday() in (4, 5):
            k *= 1.12                      # víkendy dražší
        if rnd.random() < 0.06:
            k *= 0.55                      # občasný propad = „deal"
        out.append({
            "origin": rnd.choice(origins),
            "out": d.isoformat(),
            "ret": (d + timedelta(days=nights)).isoformat(),
            "price": round(base * k / 10) * 10,
            "currency": cfg.get("currency", "CZK"),
        })
    return out


def _demo_detail(origins, dest, out_date, ret_date, cfg) -> list[dict]:
    rnd = random.Random(f"{dest}:{out_date}")
    base = _demo_base(dest)
    options = []
    for i in range(3):
        price = round(base * (0.85 + i * 0.18 + rnd.random() * 0.1) / 10) * 10
        flights = []
        for direction, day, (o, t) in (("out", out_date, (rnd.choice(origins), dest)),
                                       ("ret", ret_date, (dest, rnd.choice(origins)))):
            dep_h = rnd.randint(6, 20)
            dur = rnd.randint(110, 200) if dest not in _DEMO_LONGHAUL else rnd.randint(500, 780)
            dep = datetime.fromisoformat(day).replace(hour=dep_h, minute=rnd.choice((0, 15, 25, 40, 55)))
            arr = dep + timedelta(minutes=dur)
            al = rnd.choice(_DEMO_AIRLINES)
            flights.append({
                "price": price, "currency": cfg.get("currency", "CZK"),
                "duration": dur, "stops": 0 if i == 0 else rnd.choice((0, 1)),
                "airline": al,
                "legs": [{"airline": al,
                          "flight_number": f"{al[:2].upper()}{rnd.randint(100, 999)}",
                          "from": o, "to": t,
                          "dep": dep.isoformat(), "arr": arr.isoformat(),
                          "duration": dur}],
            })
        options.append({"price": price, "currency": cfg.get("currency", "CZK"),
                        "flights": flights})
    return options
