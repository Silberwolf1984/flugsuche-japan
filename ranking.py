"""
Bewertung von Flügen.
"""

from config import AIRLINE_PRIORITY, STAY_DAYS_TARGET
from models import Flight


def airline_priority(airline: str) -> int:
    """
    Priorität einer Airline.
    """
    return AIRLINE_PRIORITY.get(airline, 0)


def duration_difference(flight: Flight) -> int:
    """
    Abweichung vom gewünschten Aufenthalt.
    """
    return abs(flight.duration - STAY_DAYS_TARGET)


def flight_sort_key(flight: Flight):
    """
    Vergleichsschlüssel.

    Reihenfolge:

    1 Direktflug
    2 Airline
    3 Preis
    4 Aufenthaltsdauer
    5 früherer Hinflug
    """

    return (
        flight.is_direct,
        airline_priority(flight.airline),
        -flight.price,
        -duration_difference(flight),
        -flight.departure.timestamp(),
    )
