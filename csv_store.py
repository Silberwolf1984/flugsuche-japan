"""
Speichert und liest die Preis-Historie.
"""

from __future__ import annotations

import csv
from pathlib import Path

from models import Flight

CSV_FILE = Path("data/preise.csv")

FIELDNAMES = [
    "abfrage_datum",
    "hinflug",
    "rueckflug",
    "reisedauer_tage",
    "preis_pro_person_eur",
    "airline",
    "anzahl_zwischenstopps",
    "hinweis",
]


def load_history() -> list[dict]:
    """
    Liest die komplette Preis-Historie.
    """

    if not CSV_FILE.exists():
        return []

    with CSV_FILE.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def append_flight(flight: Flight) -> None:
    """
    Hängt einen Flug an die CSV an.
    """

    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)

    write_header = not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0

    with CSV_FILE.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        if write_header:
            writer.writeheader()

        writer.writerow(
            {
                "abfrage_datum": flight.query_time.strftime("%Y-%m-%d %H:%M:%S"),
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


def last_price() -> int | None:
    """
    Liefert den zuletzt gespeicherten Preis.
    """

    history = load_history()

    if not history:
        return None

    try:
        return int(history[-1]["preis_pro_person_eur"])
    except (KeyError, ValueError):
        return None


def best_price() -> int | None:
    """
    Liefert den bisher günstigsten Preis.
    """

    history = load_history()

    prices = []

    for row in history:
        try:
            prices.append(int(row["preis_pro_person_eur"]))
        except (KeyError, ValueError):
            pass

    return min(prices) if prices else None
