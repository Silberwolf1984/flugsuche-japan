"""
api.py

Kommunikation mit der TravelPayouts API.
"""

from datetime import datetime
import requests

from config import (
    API_URL,
    CURRENCY,
    DESTINATION,
    MONTH_COMBINATIONS,
    ORIGINS,
    STAY_DAYS_TARGET,
    STAY_DAYS_TOLERANCE,
    EXCLUDED_AIRLINES,
)

from models import Flight


def search_prices(token: str) -> list[Flight]:
    """
    Sucht Flüge und liefert eine Liste von Flight-Objekten.
    """

    flights: list[Flight] = []

    headers = {
        "x-access-token": token
    }

    for origin in ORIGINS:

        for depart_month, return_month in MONTH_COMBINATIONS:

            print()
            print("=" * 70)
            print(f"🔍 Suche {origin} | {depart_month} -> {return_month}")

            params = {
                "origin": origin,
                "destination": DESTINATION,
                "depart_date": depart_month,
                "return_date": return_month,
                "currency": CURRENCY,
            }

            try:

                response = requests.get(
                    API_URL,
                    headers=headers,
                    params=params,
                    timeout=30,
                )

                response.raise_for_status()

            except requests.RequestException as ex:

                print(f"❌ API-Fehler ({origin}): {ex}")
                continue

            payload = response.json()

            data = payload.get("data", {})

            if not isinstance(data, dict):
                print("❌ API liefert kein gültiges Datenformat.")
                continue

            if not data:
                print("❌ API liefert KEINE Flugdaten.")
                continue

            print(f"✅ API liefert {len(data)} Ziel(e).")

            accepted = 0

            for destination in data.values():

                if not isinstance(destination, dict):
                    continue

                for stop_key, item in destination.items():

                    airline = item.get("airline")

                    print()
                    print("-" * 60)
                    print(
                        f"Airline={airline} | "
                        f"Preis={item.get('price')} € | "
                        f"Stops={stop_key}"
                    )

                    if airline in EXCLUDED_AIRLINES:
                        print(f"❌ Verworfen: Airline {airline} ausgeschlossen.")
                        continue

                    try:

                        departure = datetime.fromisoformat(
                            item["departure_at"].replace("Z", "+00:00")
                        )

                        return_date = datetime.fromisoformat(
                            item["return_at"].replace("Z", "+00:00")
                        )

                    except Exception as ex:
                        print(f"❌ Datumsfehler: {ex}")
                        continue

                    duration = (return_date - departure).days

                    print(
                        f"Reise: {departure.date()} -> "
                        f"{return_date.date()} "
                        f"({duration} Tage)"
                    )

                    if abs(duration - STAY_DAYS_TARGET) > STAY_DAYS_TOLERANCE:
                        print(
                            f"❌ Verworfen: "
                            f"Aufenthalt {duration} Tage "
                            f"(Ziel {STAY_DAYS_TARGET}±{STAY_DAYS_TOLERANCE})"
                        )
                        continue

                    try:
                        price = int(item["price"])
                    except Exception:
                        print("❌ Preis konnte nicht gelesen werden.")
                        continue

                    link = item.get("link", "")

                    print("✅ Flug akzeptiert.")

                    accepted += 1

                    flights.append(

                        Flight(

                            origin=origin,

                            destination=DESTINATION,

                            airline=airline,

                            departure=departure,

                            return_date=return_date,

                            price=price,

                            stops=int(stop_key),

                            link=link,

                        )

                    )

            print()
            print(
                f"➡️ Ergebnis für {origin} "
                f"{depart_month}->{return_month}: "
                f"{accepted} akzeptierte Flüge"
            )

    print()
    print("=" * 70)
    print(f"GESAMT: {len(flights)} akzeptierte Flüge")
    print("=" * 70)

    return flights
