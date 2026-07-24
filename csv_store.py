"""
Speichert und lädt Flüge als CSV-Datei.
"""

from __future__ import annotations

import csv
from pathlib import Path

from models import Flight
from config import CSV_PATH


CSV_HEADER = [
    "origin",
    "destination",
    "airline",
    "departure",
    "return",
    "price",
    "stops",
    "link",
]


def csv_exists() -> bool:
    """
    Prüft, ob die CSV-Datei bereits existiert.
    """
    return Path(CSV_PATH).exists()


def write_header() -> None:
    """
    Erstellt eine neue CSV-Datei mit Kopfzeile.
    """

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)


def append_flight(flight: Flight) -> None:
    """
    Hängt einen Flug an die CSV-Datei an.
    """

    if not csv_exists():
        write_header()

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                flight.origin,
                flight.destination,
                flight.airline,
                flight.departure.isoformat(),
                flight.return_date.isoformat(),
                flight.price,
                flight.stops,
                flight.link,
            ]
        )


def load_history() -> list[dict]:
    """
    Liest die komplette CSV-Datei ein.

    Rückgabe:
        Liste aller gespeicherten Datensätze.
    """

    if not csv_exists():
        return []

    with open(CSV_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def last_price(origin: str) -> int | None:
    """
    Liefert den zuletzt gespeicherten Preis
    für einen Abflughafen.
    """

    history = load_history()

    for row in reversed(history):
        if row["origin"] == origin:
            try:
                return int(row["price"])
            except ValueError:
                return None

    return None


def best_price(origin: str) -> int | None:
    """
    Liefert den bisher günstigsten Preis
    für einen Abflughafen.
    """

    history = load_history()

    prices = []

    for row in history:
        if row["origin"] == origin:
            try:
                prices.append(int(row["price"]))
            except ValueError:
                pass

    if not prices:
        return None

    return min(prices)
