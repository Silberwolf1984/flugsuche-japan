"""
api.py

Kommunikation mit der TravelPayouts API.
Version 2.0
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


# ============================================================
# Einstellungen
# ============================================================

# Für normale Nutzung False lassen.
# Bei Problemen einfach auf True setzen.
DEBUG = True


# ============================================================
# Hilfsfunktionen
# ============================================================

def debug(text: str) -> None:
    """Gibt Debugmeldungen aus."""

    if DEBUG:
        print(text)


def print_separator() -> None:
    """Schöne Trennlinie."""

    if DEBUG:
        print("=" * 70)


# ============================================================
# API
# ============================================================

def search_prices(token: str) -> list[Flight]:
    """
    Sucht Flüge über die TravelPayouts API.
    """

    flights: list[Flight] = []

    headers = {
        "x-access-token": token
    }

    # --------------------------------------------------------
    # Statistik
    # --------------------------------------------------------

    total_api_results = 0
    accepted_results = 0

    excluded_airlines = 0
    wrong_duration = 0
    invalid_dates = 0
    invalid_price = 0
    empty_results = 0

    airlines_found: dict[str, int] = {}

    cheapest_price = None
    cheapest_airline = None

    # --------------------------------------------------------

    for origin in ORIGINS:

        for depart_month, return_month in MONTH_COMBINATIONS:

            print_separator()

            debug(
                f"🔍 Suche {origin} | "
                f"{depart_month} -> {return_month}"
            )

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

                debug("❌ Ungültige API-Antwort.")

                continue

            if not data:

                empty_results += 1

                debug("❌ API liefert keine Flugdaten.")

                continue

            debug(f"✅ {len(data)} Ziel(e) erhalten.")

            accepted_this_query = 0
                        for destination in data.values():

                if not isinstance(destination, dict):
                    continue

                for stop_key, item in destination.items():

                    total_api_results += 1

                    airline = item.get("airline", "?")

                    airlines_found[airline] = (
                        airlines_found.get(airline, 0) + 1
                    )

                    debug("")
                    debug("-" * 60)
                    debug(
                        f"Airline={airline} | "
                        f"Preis={item.get('price')} € | "
                        f"Stops={stop_key}"
                    )

                    # -----------------------------------------
                    # Airline ausgeschlossen?
                    # -----------------------------------------

                    if airline in EXCLUDED_AIRLINES:

                        excluded_airlines += 1

                        debug(
                            f"❌ Airline {airline} ausgeschlossen."
                        )

                        continue

                    # -----------------------------------------
                    # Datum lesen
                    # -----------------------------------------

                    try:

                        departure = datetime.fromisoformat(
                            item["departure_at"].replace(
                                "Z",
                                "+00:00",
                            )
                        )

                        return_date = datetime.fromisoformat(
                            item["return_at"].replace(
                                "Z",
                                "+00:00",
                            )
                        )

                    except Exception:

                        invalid_dates += 1

                        debug("❌ Datum ungültig.")

                        continue

                    duration = (
                        return_date - departure
                    ).days

                    debug(
                        f"Reise: "
                        f"{departure.date()} -> "
                        f"{return_date.date()} "
                        f"({duration} Tage)"
                    )

                    # -----------------------------------------
                    # Aufenthaltsdauer
                    # -----------------------------------------

                    if (
                        abs(
                            duration
                            - STAY_DAYS_TARGET
                        )
                        > STAY_DAYS_TOLERANCE
                    ):

                        wrong_duration += 1

                        debug(
                            f"❌ Aufenthalt "
                            f"{duration} Tage "
                            f"(gewünscht "
                            f"{STAY_DAYS_TARGET}"
                            f"±{STAY_DAYS_TOLERANCE})"
                        )

                        continue

                    # -----------------------------------------
                    # Preis
                    # -----------------------------------------

                    try:

                        price = int(item["price"])

                    except Exception:

                        invalid_price += 1

                        debug(
                            "❌ Preis ungültig."
                        )

                        continue

                    if (
                        cheapest_price is None
                        or price < cheapest_price
                    ):

                        cheapest_price = price
                        cheapest_airline = airline

                    link = item.get("link", "")

                    accepted_results += 1
                    accepted_this_query += 1

                    debug("✅ Flug akzeptiert.")

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

            debug("")
            debug(
                f"➡️ Ergebnis: "
                f"{accepted_this_query} "
                f"Flüge akzeptiert."
            )
                # ========================================================
    # Statistik
    # ========================================================

    print_separator()

    print("📊 TravelPayouts Statistik")
    print()

    print(f"API-Treffer insgesamt      : {total_api_results}")
    print(f"Akzeptierte Flüge          : {accepted_results}")
    print(f"Keine API-Daten            : {empty_results}")
    print(f"Airlines ausgeschlossen    : {excluded_airlines}")
    print(f"Aufenthaltsdauer unpassend : {wrong_duration}")
    print(f"Ungültige Datensätze       : {invalid_dates}")
    print(f"Ungültiger Preis           : {invalid_price}")

    print()

    if airlines_found:

        print("Gefundene Airlines:")

        for airline in sorted(airlines_found):

            print(
                f"  {airline}: "
                f"{airlines_found[airline]} Treffer"
            )

    else:

        print("Keine Airlines gefunden.")

    print()

    if cheapest_price is not None:

        print(
            f"💰 Günstigster API-Treffer: "
            f"{cheapest_price} € "
            f"({cheapest_airline})"
        )

    else:

        print("💰 Kein gültiger Preis gefunden.")

    print_separator()

    if accepted_results == 0:

        print()
        print("⚠️ Die API hat Flüge geliefert,")
        print("aber keiner erfüllt alle Filter.")
        print()

        print("Mögliche Ursachen:")

        if excluded_airlines:
            print(
                f" • {excluded_airlines} Flug/Flüge "
                "wurden wegen ausgeschlossener Airlines verworfen."
            )

        if wrong_duration:
            print(
                f" • {wrong_duration} Flug/Flüge "
                "hatten eine unpassende Aufenthaltsdauer."
            )

        if empty_results:
            print(
                f" • {empty_results} Suchkombination(en) "
                "lieferten überhaupt keine Cache-Daten."
            )

        print()

    return flights
