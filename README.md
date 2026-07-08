# Flight Radar ✈

Osobní radar na nejlevnější letenky z PRG / VIE / BRQ. Lokální webová aplikace —
FastAPI backend + dashboard ve stylu letištní odletové tabule (split-flap).

Data bere z **Google Flights** přes knihovnu [`fli`](https://pypi.org/project/flights/)
(PyPI balík se jmenuje `flights`, importuje se jako `fli`). Bez API klíče, zdarma.

> ⚠️ **Riziko:** `fli` mluví s neoficiálním interním endpointem Google Flights.
> Když Google změní formát, je potřeba knihovnu updatnout (`pip install -U flights`).
> Pro osobní použití na localhostu OK. Záloha: balík `fast-flights`.

## Tři režimy

| Režim | Co dělá |
|---|---|
| **Kamkoliv** | ~40 kurátorských destinací (`destinations.py`), nejlevnější round-trip v okně 90 dní |
| **Watchlist** | tvoje destinace z `config.json` s cílovou cenou → chip „deal pod limit" |
| **Víkend** | 2 noci, odlet jen Pá/So, city breaky |

## Spuštění

```bash
cd flight-radar
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# náhled bez sítě (syntetická data):
FLIGHT_RADAR_DEMO=1 uvicorn app:app --reload --port 8000

# ostrý režim (živé ceny z Google Flights):
uvicorn app:app --reload --port 8000
```

→ otevři **http://localhost:8000**

První načtení každého režimu spustí vyhledávání samo. Hledá se **každé domácí
letiště zvlášť** — kombinovaný dotaz (PRG+VIE+BRQ najednou) vrací od Googlu jen
zlomek cenové mřížky, takže by ceny neseděly. V ostrém režimu jdou requesty
sekvenčně s prodlevou ~1,8 s (slušnost k endpointu, jinak hrozí CAPTCHA):
„Kamkoliv" = 44 destinací × 3 letiště ≈ **7 minut**, watchlist ≈ 2 min.
Průběh vidíš v hlavičce; víc režimů najednou se řadí do fronty (nikdy se
nehledá paralelně). Výsledky se kešují v SQLite (`radar.db`) na 8 hodin,
takže se to platí jen jednou za den.

## Filtry

Aplikace si při aktualizaci ukládá **celou cenovou mřížku** (cena pro každý den
× letiště), takže tyhle filtry fungují okamžitě, bez nového hledání:

- **Termín odletu** — kdykoliv / konkrétní měsíc / vlastní rozmezí dat
- **Den odletu** — po–ne (např. jen Pá+So)
- **Letiště** — PRG / VIE / BRQ
- **Max cena** a **řazení** (cena / datum / destinace)

Filtry označené ↻ (**přestupy**, **počet nocí**) mění, co se u Googlu hledá,
a projeví se až při další aktualizaci.

## Nastavení (`config.json`)

- `watchlist` — destinace, počet nocí, cílová cena (CZK)
- `search_window_days` — jak daleko dopředu hledat (default 90)
- `cache_ttl_hours`, `request_delay_seconds` — cache a tempo requestů
- `anywhere.nights`, `weekend.nights`, `weekend.depart_days`

## Architektura

```
app.py            FastAPI: dashboard + API, refresh v background threadu
flightsearch.py   obálky nad fli (SearchDates / SearchFlights) + DEMO data
store.py          SQLite cache s TTL + stav jobů
destinations.py   ~40 destinací pro režim „Kamkoliv"
static/index.html dashboard (vanilla JS, žádný build step)
```

API: `GET /api/config` · `GET /api/deals?mode=` · `POST /api/refresh` ·
`GET /api/status?mode=` · `GET /api/detail?origins=&dest=&out=&ret=`
