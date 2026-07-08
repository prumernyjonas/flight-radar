# Flight Radar — FastAPI backend: servíruje dashboard + API, orchestruje refresh.
import json
import threading
import time
import traceback
from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import flightsearch
import store
from destinations import DESTINATIONS, WEEKEND_DESTINATIONS

BASE = Path(__file__).parent
CONFIG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))

MODES = ("anywhere", "watchlist", "weekend")
VALID_STOPS = ("ANY", "NON_STOP", "ONE_STOP_OR_FEWER", "TWO_OR_FEWER_STOPS")
ALL_ORIGINS = CONFIG["anywhere"]["origins"]

app = FastAPI(title="Flight Radar")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/config")
def api_config():
    return {**CONFIG, "demo": flightsearch.DEMO, "modes": MODES}


@app.get("/api/deals")
def api_deals(mode: str = "anywhere"):
    _check_mode(mode)
    deals, params, updated_at, fresh = store.load_deals(mode, CONFIG["cache_ttl_hours"])
    # cache z demo režimu nesmí prosáknout do ostrého (a naopak)
    if deals and params.get("demo") != flightsearch.DEMO:
        deals, fresh, updated_at = [], False, None
    return {"mode": mode, "deals": deals, "params": params,
            "updated_at": updated_at, "fresh": fresh}


class RefreshBody(BaseModel):
    mode: str
    origins: list[str] | None = None   # podmnožina domácích letišť
    max_stops: str | None = None       # ANY | NON_STOP | ...


@app.post("/api/refresh")
def api_refresh(body: RefreshBody):
    _check_mode(body.mode)
    origins = [o for o in (body.origins or ALL_ORIGINS) if o in ALL_ORIGINS] or ALL_ORIGINS
    stops = body.max_stops if body.max_stops in VALID_STOPS else None

    tasks = _build_tasks(body.mode)
    if not store.job_start(body.mode, len(tasks)):
        return {"started": False, "status": store.job_status(body.mode)}

    t = threading.Thread(target=_run_refresh, args=(body.mode, tasks, origins, stops),
                         daemon=True)
    t.start()
    return {"started": True, "status": store.job_status(body.mode)}


@app.get("/api/status")
def api_status(mode: str = "anywhere"):
    _check_mode(mode)
    return store.job_status(mode)


@app.get("/api/detail")
def api_detail(origins: str, dest: str, out: str, ret: str, stops: str = "ANY"):
    """Detail letů pro konkrétní datum (on-demand po rozkliknutí karty)."""
    origin_list = [o for o in origins.split(",") if o in ALL_ORIGINS] or ALL_ORIGINS
    if stops not in VALID_STOPS:
        stops = "ANY"
    try:
        options = flightsearch.route_detail(origin_list, dest, out, ret, stops, CONFIG)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Vyhledání detailu selhalo: {e}")
    return {"options": options}


# ------------------------------------------------------------------ refresh job

def _check_mode(mode: str):
    if mode not in MODES:
        raise HTTPException(status_code=400, detail=f"Neznámý režim: {mode}")


def _build_tasks(mode: str) -> list[dict]:
    """Seznam úloh (jedna úloha = jedna destinace = jeden request)."""
    if mode == "watchlist":
        return [{"dest": w["dest"], "label": w["label"], "nights": w["nights"],
                 "target_price": w["target_price"], "country": None, "region": "watchlist"}
                for w in CONFIG["watchlist"]]
    src = WEEKEND_DESTINATIONS if mode == "weekend" else DESTINATIONS
    nights = CONFIG["weekend" if mode == "weekend" else "anywhere"]["nights"]
    return [{"dest": d["iata"], "label": d["city"], "nights": nights,
             "target_price": None, "country": d["country"], "region": d["region"]}
            for d in src]


# serializace refresh jobů napříč režimy — nikdy nechceme na Google
# střílet z více vláken najednou (CAPTCHA/ban)
_search_lock = threading.Lock()


def _run_refresh(mode: str, tasks: list[dict], origins: list[str], stops_override: str | None):
    """Background refresh: sekvenčně, s prodlevou (slušnost k endpointu).
    Chyba na jedné trase nesmí shodit celý běh."""
    with _search_lock:
        _run_refresh_locked(mode, tasks, origins, stops_override)


def _run_refresh_locked(mode: str, tasks: list[dict], origins: list[str], stops_override: str | None):
    stops = stops_override or CONFIG["weekend" if mode == "weekend" else "anywhere"].get("max_stops", "ANY")
    window = CONFIG["search_window_days"]
    delay = 0 if flightsearch.DEMO else CONFIG["request_delay_seconds"]
    deals, errors = [], 0

    for task in tasks:
        try:
            dates = flightsearch.search_dates(origins, task["dest"], task["nights"],
                                              window, stops, CONFIG)
            if mode == "weekend":
                # filtr client-side: odlety jen Pá/So
                allowed = {"FRI": 4, "SAT": 5}
                days = {allowed[d] for d in CONFIG["weekend"]["depart_days"] if d in allowed}
                dates = [d for d in dates if date.fromisoformat(d["out"]).weekday() in days]
            if dates:
                best = min(dates, key=lambda d: d["price"])
                deals.append(_make_deal(mode, task, origins, best))
        except Exception:
            errors += 1
            traceback.print_exc()
        finally:
            store.job_progress(mode)
        if delay:
            time.sleep(delay)

    deals.sort(key=lambda d: d["price"])
    store.save_deals(mode, deals, {"origins": origins, "max_stops": stops,
                                   "window_days": window, "errors": errors,
                                   "demo": flightsearch.DEMO})
    store.job_finish(mode, error=f"{errors} tras selhalo" if errors else None)


def _make_deal(mode: str, task: dict, origins: list[str], best: dict) -> dict:
    target = task["target_price"]
    origin = best.get("origin") or origins[0]  # konkrétní letiště nejlevnější ceny
    return {
        "origin": origin,
        "origins": origins,
        "dest": task["dest"],
        "label": task["label"],
        "country": task["country"],
        "region": task["region"],
        "nights": task["nights"],
        "out": best["out"],
        "ret": best["ret"],
        "price": best["price"],
        "currency": best["currency"],
        "target_price": target,
        "is_deal": bool(target and best["price"] <= target),
        "url": _gflights_url(origin, task["dest"], best["out"], best["ret"]),
    }


def _gflights_url(orig: str, dest: str, out: str, ret: str | None) -> str:
    q = f"Flights from {orig} to {dest} on {out}"
    if ret:
        q += f" through {ret}"
    return "https://www.google.com/travel/flights?q=" + quote(q)
