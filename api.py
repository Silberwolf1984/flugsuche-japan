"""
api.py
Kommunikation mit der TravelPayouts API.
"""

import time
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

# Anzahl Versuche und Wartezeit (Sekunden) bei vorübergehenden Fehlern
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def _request_with_retry(headers: dict, params: dict) -> dict | None:
    """
    Führt eine API-Anfrage aus und wiederholt sie bei vorübergehenden
    Fehlern (Netzwerkfehler, Rate-Limit, Serverfehler).

    Gibt das geparste JSON zurück oder None, wenn alle Versuche
    fehlschlagen bzw. die API einen dauerhaften Fehler meldet.
    """
    origin = params.get("origin")
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                API_URL,
                headers=headers,
                params=params,
                timeout=30,
            )
        except requests.RequestException as ex:
            last_error = str(ex)
            print(f"⚠️ Netzwerkfehler ({origin}, Versuch {attempt}/{MAX_RETRIES}): {ex}")
        else:
            # Rate-Limit oder Serverfehler -> es lohnt sich, es erneut zu versuchen
            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}"
                print(f"⚠️ {last_error} ({origin}, Versuch {attempt}/{MAX_RETRIES})")
            else:
                try:
                    response.raise_for_status()
                except requests.RequestException as ex:
                    # Dauerhafter Fehler (z.B. 400/401/403) -> kein erneuter Versuch
                    print(f"❌ API-Fehler ({origin}): {ex}")
                    return None

                payload = response.json()
                if not payload.get("success", True):
                    print(f"⚠️ TravelPayouts meldet success=false ({origin})")
                    return None

                return payload

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    print(f"❌ Alle {MAX_RETRIES} Versuche fehlgeschlagen ({origin}): {last_error}")
    return None


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

            payload = _request_with_retry(headers, params)
            if payload is None:
                continue

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
