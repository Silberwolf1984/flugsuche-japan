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

                print(f"API-Fehler ({origin}): {ex}")
                continue

            payload = response.json()

            data = payload.get("data", {})

            if not isinstance(data, dict):
                continue

            for destination in data.values():

                if not isinstance(destination, dict):
                    continue

                for stop_key, item in destination.items():

                    airline = item.get("airline")

                    if airline in EXCLUDED_AIRLINES:
                        continue

                    try:

                        departure = datetime.fromisoformat(
                            item["departure_at"].replace("Z", "+00:00")
                        )

                        return_date = datetime.fromisoformat(
                            item["return_at"].replace("Z", "+00:00")
                        )

                    except Exception:
                        continue

                    duration = (return_date - departure).days

                    if abs(duration - STAY_DAYS_TARGET) > STAY_DAYS_TOLERANCE:
                        continue

                    try:
                        price = int(item["price"])
                    except Exception:
                        continue

                    link = item.get("link", "")

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

    return flights
