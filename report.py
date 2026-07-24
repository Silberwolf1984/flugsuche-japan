"""
report.py

Ausgabe der gefundenen Flüge.
"""

from models import Flight


def print_header() -> None:
    """Gibt eine Überschrift aus."""

    print()
    print("=" * 70)
    print("          🇯🇵 Japan Flight Monitor")
    print("=" * 70)
    print()


def print_flight(flight: Flight) -> None:
    """
    Gibt einen einzelnen Flug formatiert aus.
    """

    print(f"✈️  {flight.origin} → {flight.destination}")
    print(f"🏷️  Airline      : {flight.airline}")
    print(f"💶 Preis         : {flight.price} €")
    print(f"📅 Hinflug       : {flight.departure:%d.%m.%Y}")
    print(f"📅 Rückflug      : {flight.return_date:%d.%m.%Y}")
    print(f"🛏️ Aufenthalt    : {flight.duration} Tage")

    if flight.is_direct:
        print("🛫 Verbindung    : Direktflug")
    else:
        print(f"🛫 Verbindung    : {flight.stops} Zwischenstopp(s)")

    if flight.link:
        print(f"🔗 Link          : {flight.link}")

    print("-" * 70)


def print_summary(flights: list[Flight]) -> None:
    """
    Gibt alle gefundenen Flüge aus.
    """

    if not flights:
        print("❌ Keine passenden Flüge gefunden.")
        return

    print_header()

    for flight in flights:
        print_flight(flight)

    print()
    print(f"✅ Insgesamt {len(flights)} passende Flüge gefunden.")
    print()
