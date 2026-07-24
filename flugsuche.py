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

    token = os.getenv("TP_API_TOKEN")

    if not token:
        print("❌ Umgebungsvariable TP_API_TOKEN nicht gesetzt.")
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
    # Ausgabe
    #
    print_summary(flights)

    #
    # CSV speichern
    #
    for flight in flights:
        append_flight(flight)

    print("💾 Flüge wurden gespeichert.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
