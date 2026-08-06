"""
flugsuche.py
Hauptprogramm des Japan Flight Monitors.
"""

import os
import sys

from api import search_prices
from csv_store import append_flight
from ranking import flight_sort_key
from report import print_summary


def main() -> int:
    """
    Einstiegspunkt des Programms.
    """
    token = (
        os.getenv("TRAVELPAYOUTS_TOKEN")
        or os.getenv("TP_API_TOKEN")
    )

    if not token:
        print("❌ Kein TravelPayouts API-Token gefunden.")
        return 1

    print("🔍 Suche nach Flügen...")
    flights = search_prices(token)

    if not flights:
        print("❌ Keine passenden Flüge gefunden.")
        return 0

    #
    # Beste Flüge zuerst
    #
    flights.sort(
        key=flight_sort_key,
        reverse=True,
    )

    #
    # Nur den besten Flug je Abflughafen behalten
    #
    best_flights = []
    seen_origins = set()
    for flight in flights:
        if flight.origin not in seen_origins:
            best_flights.append(flight)
            seen_origins.add(flight.origin)
    flights = best_flights

    #
    # Ausgabe
    #
    print_summary(flights)

    #
    # CSV speichern (nur bei tatsächlichen Änderungen)
    #
    saved = 0
    for flight in flights:
        if append_flight(flight):
            saved += 1

    if saved:
        print(f"💾 {saved} neue/geänderte Flugpreis(e) wurden gespeichert.")
    else:
        print("ℹ️ Keine Preisänderungen seit dem letzten Lauf – nichts gespeichert.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
