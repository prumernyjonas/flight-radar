# SQLite cache dealů (s TTL) + in-memory stav běžících refresh jobů.
import json
import sqlite3
import threading
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "radar.db"

_db_lock = threading.Lock()


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute(
        "CREATE TABLE IF NOT EXISTS cache ("
        " mode TEXT PRIMARY KEY,"
        " payload TEXT NOT NULL,"
        " params TEXT NOT NULL,"
        " updated_at REAL NOT NULL)"
    )
    return c


def save_deals(mode: str, deals: list, params: dict) -> None:
    """Uloží výsledky refreshe pro daný režim (přepíše starší)."""
    with _db_lock, _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO cache (mode, payload, params, updated_at) VALUES (?,?,?,?)",
            (mode, json.dumps(deals, ensure_ascii=False), json.dumps(params), time.time()),
        )


def load_deals(mode: str, ttl_hours: float):
    """Vrátí (deals, params, updated_at, fresh). Prázdná cache -> ([], {}, None, False)."""
    with _db_lock, _conn() as c:
        row = c.execute(
            "SELECT payload, params, updated_at FROM cache WHERE mode=?", (mode,)
        ).fetchone()
    if not row:
        return [], {}, None, False
    payload, params, updated_at = row
    fresh = (time.time() - updated_at) < ttl_hours * 3600
    return json.loads(payload), json.loads(params), updated_at, fresh


# ---------- stav refresh jobů (jen v paměti, jeden job na režim) ----------

_jobs_lock = threading.Lock()
_jobs: dict[str, dict] = {}


def job_start(mode: str, total: int) -> bool:
    """Zaregistruje job; vrátí False, pokud už pro režim běží."""
    with _jobs_lock:
        j = _jobs.get(mode)
        if j and j["running"]:
            return False
        _jobs[mode] = {"running": True, "total": total, "done": 0, "error": None,
                       "started_at": time.time(), "finished_at": None}
        return True


def job_progress(mode: str) -> None:
    with _jobs_lock:
        if mode in _jobs:
            _jobs[mode]["done"] += 1


def job_finish(mode: str, error: str | None = None) -> None:
    with _jobs_lock:
        if mode in _jobs:
            _jobs[mode].update(running=False, error=error, finished_at=time.time())


def job_status(mode: str) -> dict:
    with _jobs_lock:
        j = _jobs.get(mode)
        return dict(j) if j else {"running": False, "total": 0, "done": 0, "error": None,
                                  "started_at": None, "finished_at": None}
