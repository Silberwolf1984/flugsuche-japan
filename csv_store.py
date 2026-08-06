"""
Speichert und liest die Preis-Historie.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from models import Flight

CSV_FILE = Path("data/preise.csv")

FIELDNAMES = [
    "abfrage_datum",
    "abflughafen",
    "hinflug",
    "rueckflug",
    "reisedauer_tage",
    "preis_pro_person_eur",
    "airline",
    "anzahl_zwischenstopps",
    "hinweis",
]


def load_history() -> list[dict]:
    """Liest die Preis-Historie."""
    if not CSV_FILE.exists():
        return []
    with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _last_entry_for_origin(origin: str) -> dict | None:
    """Liefert den zuletzt gespeicherten Eintrag für einen Abflughafen."""
    for row in reversed(load_history()):
        if row.get("abflughafen") == origin:
            return row
    return None


def has_changed(flight: Flight) -> bool:
    """
    Prüft, ob sich der Flug gegenüber dem letzten gespeicherten
    Eintrag für denselben Abflughafen unterscheidet.

    Nur bei Preis-, Airline-, Datums- oder Stopp-Änderungen lohnt
    sich ein neuer CSV-Eintrag.
    """
    last = _last_entry_for_origin(flight.origin)
    if last is None:
        return True

    try:
        last_price = int(last["preis_pro_person_eur"])
    except (KeyError, ValueError):
        return True

    return (
        last_price != flight.price
        or last.get("airline") != flight.airline
        or last.get("hinflug") != flight.departure.strftime("%Y-%m-%d")
        or last.get("rueckflug") != flight.return_date.strftime("%Y-%m-%d")
        or last.get("anzahl_zwischenstopps") != str(flight.stops)
    )


def append_flight(flight: Flight, force: bool = False) -> bool:
    """
    Speichert einen Flug in der CSV, falls sich gegenüber dem letzten
    Eintrag für diesen Abflughafen etwas geändert hat.

    Gibt True zurück, wenn tatsächlich ein neuer Eintrag geschrieben wurde.
    Mit force=True wird immer geschrieben (z.B. für einen erzwungenen
    täglichen Log-Eintrag).
    """
    if not force and not has_changed(flight):
        return False

    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_header = not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0

    with CSV_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "abfrage_datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "abflughafen": flight.origin,
                "hinflug": flight.departure.strftime("%Y-%m-%d"),
                "rueckflug": flight.return_date.strftime("%Y-%m-%d"),
                "reisedauer_tage": flight.duration,
                "preis_pro_person_eur": flight.price,
                "airline": flight.airline,
                "anzahl_zwischenstopps": flight.stops,
                "hinweis": (
                    "Direktflug"
                    if flight.is_direct
                    else f"{flight.stops} Zwischenstopp(e)"
                ),
            }
        )
    return True


def last_price(origin: str | None = None) -> int | None:
    """
    Liefert den zuletzt gespeicherten Preis.
    Optional gefiltert nach Abflughafen.
    """
    history = load_history()
    if origin is not None:
        history = [row for row in history if row.get("abflughafen") == origin]
    if not history:
        return None
    try:
        return int(history[-1]["preis_pro_person_eur"])
    except (KeyError, ValueError):
        return None


def best_price(origin: str | None = None) -> int | None:
    """
    Liefert den günstigsten bisher gespeicherten Preis.
    Optional gefiltert nach Abflughafen.
    """
    history = load_history()
    if origin is not None:
        history = [row for row in history if row.get("abflughafen") == origin]

    prices = []
    for row in history:
        try:
            prices.append(int(row["preis_pro_person_eur"]))
        except (KeyError, ValueError):
            pass
    return min(prices) if prices else None
