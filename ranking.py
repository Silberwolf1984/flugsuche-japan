"""
Bewertung und Vergleich von Flügen.

Diese Datei enthält ausschließlich Logik zur Auswahl des besten Fluges.
Sie kennt weder die API noch CSV-Dateien.
"""

from datetime import datetime

from config import AIRLINE_PRIORITY


def airline_priority(airline: str) -> int:
    """
    Liefert die Priorität einer Airline.

    Höhere Werte bedeuten eine höhere Bevorzugung.
    Unbekannte Airlines erhalten 0 Punkte.
    """
    return AIRLINE_PRIORITY.get(airline, 0)


def is_direct_flight(stop_key: str) -> bool:
    """
    True, wenn es sich um einen Direktflug handelt.
    """
    return stop_key == "0"


def departure_timestamp(flight: dict) -> float:
    """
    Zeitstempel des Hinfluges.

    Wird genutzt, um bei identischen Flügen den früheren
    Abflug zu bevorzugen.
    """
    try:
        dep = flight["departure_at"].replace("Z", "+00:00")
        return datetime.fromisoformat(dep).timestamp()
    except Exception:
        return float("inf")


def trip_duration(flight: dict) -> int:
    """
    Aufenthaltsdauer in Tagen.

    Falls keine Berechnung möglich ist,
    wird eine sehr große Zahl zurückgegeben.
    """
    try:
        dep = datetime.fromisoformat(
            flight["departure_at"].replace("Z", "+00:00")
        )
        ret = datetime.fromisoformat(
            flight["return_at"].replace("Z", "+00:00")
        )

        return (ret - dep).days

    except Exception:
        return 999


def flight_sort_key(stop_key: str, flight: dict):
    """
    Erstellt einen Vergleichsschlüssel.

    Reihenfolge der Bewertung:

        1. Direktflug
        2. Airline
        3. Preis
        4. Aufenthaltsdauer
        5. früherer Hinflug

    Kann direkt mit

        max(..., key=flight_sort_key)

    verwendet werden.
    """

    airline = flight.get("airline", "")
    price = int(flight.get("price", 999999))

    return (

        # Direktflug gewinnt immer
        is_direct_flight(stop_key),

        # Airline-Ranking
        airline_priority(airline),

        # günstiger gewinnt
        -price,

        # kürzere Abweichung gewinnt
        -trip_duration(flight),

        # früherer Flug gewinnt
        -departure_timestamp(flight),
    )


def better_flight(
    current_stop_key: str,
    current_flight: dict,
    best_stop_key: str,
    best_flight: dict,
) -> bool:
    """
    Vergleicht zwei Flüge.

    True bedeutet:

        current_flight ist besser als best_flight.
    """

    return (
        flight_sort_key(current_stop_key, current_flight)
        >
        flight_sort_key(best_stop_key, best_flight)
    )
