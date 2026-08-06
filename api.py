"""
api.py
Kommunikation mit der TravelPayouts API (Preiskalender).
"""

import time
from datetime import datetime

import requests

from config import (
    CALENDAR_API_URL,
    CURRENCY,
    DESTINATION,
    SEARCH_MONTHS,
    ORIGINS,
    STAY_DAYS_TARGET,
    DURATION_SAFETY_MARGIN_DAYS,
    EXCLUDED_AIRLINES,
    DEBUG,
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
                CALENDAR_API_URL,
                headers=headers,
                params=params,
                timeout=30,
            )
        except requests.RequestException as ex:
            last_error = str(ex)
            print(f"⚠️ Netzwerkfehler ({origin}, Versuch {attempt}/{MAX_RETRIES}): {ex}")
        else:
            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}"
                print(f"⚠️ {last_error} ({origin}, Versuch {attempt}/{MAX_RETRIES})")
            else:
                try:
                    response.raise_for_status()
                except requests.RequestException as ex:
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
    Sucht Flüge über den Preiskalender-Endpunkt und liefert eine Liste
    von Flight-Objekten.

    Der Kalender wird pro Origin und pro Monat abgefragt und liefert
    den günstigsten Preis für JEDEN Tag des Monats, jeweils für einen
    Aufenthalt von exakt STAY_DAYS_TARGET Tagen.
    """
    flights: list[Flight] = []
    headers = {
        "x-access-token": token
    }

    # Statistik zur Diagnose, warum ggf. keine Flüge übrig bleiben
    stats = {
        "anfragen": 0,
        "rohtreffer": 0,
        "verworfen_airline": 0,
        "verworfen_dauer": 0,
        "verworfen_preis": 0,
        "uebernommen": 0,
    }

    for origin in ORIGINS:
        for month in SEARCH_MONTHS:
            params = {
                "origin": origin,
                "destination": DESTINATION,
                "depart_date": month,
                "calendar_type": "departure_date",
                "length": STAY_DAYS_TARGET,
                "currency": CURRENCY,
            }

            stats["anfragen"] += 1
            payload = _request_with_retry(headers, params)
            if payload is None:
                continue

            data = payload.get("data", {})
            if not isinstance(data, dict):
                if DEBUG:
                    print(f"🐛 {origin} {month}: keine 'data' im Payload")
                continue

            if DEBUG and not data:
                print(f"🐛 {origin} {month}: 'data' ist leer (API hat für diesen Monat nichts gefunden)")

            # data ist hier ein dict: {"2027-02-01": {...}, "2027-02-02": {...}, ...}
            for date_key, item in data.items():
                if not isinstance(item, dict):
                    continue

                stats["rohtreffer"] += 1
                airline = item.get("airline")

                if airline in EXCLUDED_AIRLINES:
                    stats["verworfen_airline"] += 1
                    if DEBUG:
                        print(f"🐛 {origin} {month} ({date_key}): Airline {airline} ausgeschlossen")
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

                # Plausibilitäts-Check: sollte durch "length" schon exakt
                # STAY_DAYS_TARGET sein, kleine Marge für Rundungsfälle.
                duration = (return_date - departure).days
                if abs(duration - STAY_DAYS_TARGET) > DURATION_SAFETY_MARGIN_DAYS:
                    stats["verworfen_dauer"] += 1
                    if DEBUG:
                        print(
                            f"🐛 {origin} {month} ({date_key}): "
                            f"{airline} gefunden, aber Aufenthalt {duration} Tage "
                            f"(erwartet: {STAY_DAYS_TARGET} ±{DURATION_SAFETY_MARGIN_DAYS}), "
                            f"Preis {item.get('price')} {CURRENCY}"
                        )
                    continue

                try:
                    price = int(item["price"])
                except Exception:
                    stats["verworfen_preis"] += 1
                    continue

                stops = item.get("transfers", 0)
                link = item.get("link", "")

                flights.append(
                    Flight(
                        origin=origin,
                        destination=DESTINATION,
                        airline=airline,
                        departure=departure,
                        return_date=return_date,
                        price=price,
                        stops=int(stops),
                        link=link,
                    )
                )
                stats["uebernommen"] += 1

    print(
        f"📊 Suche abgeschlossen: {stats['anfragen']} Anfragen, "
        f"{stats['rohtreffer']} Rohtreffer, "
        f"{stats['verworfen_airline']} wegen Airline verworfen, "
        f"{stats['verworfen_dauer']} wegen Aufenthaltsdauer verworfen, "
        f"{stats['verworfen_preis']} wegen ungültigem Preis verworfen, "
        f"{stats['uebernommen']} übernommen."
    )

    return flights
