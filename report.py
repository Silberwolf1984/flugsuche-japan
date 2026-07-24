"""
Ausgabe der gefundenen Flüge.
"""

from models import Flight
from csv_store import last_price, best_price


def print_header() -> None:
    """Gibt eine Überschrift aus."""

    print()
    print("=" * 70)
    print("          🇯🇵 Japan Flight Monitor")
    print("=" * 70)
    print()


def print_flight(
    flight: Flight,
    old_price: int | None = None,
    best: int | None = None,
) -> None:
    """
    Gibt einen einzelnen Flug formatiert aus.
    """

    print(f"✈️  {flight.origin} → {flight.destination}")
    print(f"🏷️  Airline      : {flight.airline}")
    print(f"💶 Preis         : {flight.price} €")

    # Preisänderung zur letzten Suche
    if old_price is not None:
        diff = flight.price - old_price

        if diff < 0:
            print(f"📉 Änderung      : {abs(diff)} € günstiger")
        elif diff > 0:
            print(f"📈 Änderung      : {diff} € teurer")
        else:
            print("➡️ Änderung      : unverändert")

    # Historischer Bestpreis
    if best is not None:
        if flight.price < best:
            print("🥇 Neuer Bestpreis!")
        elif flight.price == best:
            print(f"🥇 Aktueller Bestpreis ({best} €)")
        else:
            diff = flight.price - best
            print(f"🏆 Bestpreis     : {best} € (+{diff} €)")

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

    # Historie nur einmal laden
    old_price = last_price()
    best = best_price()

    for flight in flights:
        print_flight(
            flight,
            old_price=old_price,
            best=best,
        )

    print()
    print(f"✅ Insgesamt {len(flights)} passende Flüge gefunden.")
    print()
