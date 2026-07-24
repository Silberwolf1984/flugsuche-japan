"""
Tägliche Preissuche für Direktflüge Frankfurt (FRA) -> Tokyo Haneda (HND)
für 2 Personen, Economy & Premium Economy, verschiedene Datumskombinationen
im Feb/März 2027 mit ca. 23 Tagen Aufenthalt.

Nutzt die Amadeus Self-Service "Flight Offers Search" API (Testumgebung,
kostenloses Kontingent).

Benötigt zwei Umgebungsvariablen:
  AMADEUS_CLIENT_ID
  AMADEUS_CLIENT_SECRET

Schreibt/erweitert eine CSV-Datei unter data/preise.csv mit allen Treffern.
"""

import os
import csv
import sys
from datetime import date, timedelta
import requests

AMADEUS_BASE_URL = "https://test.api.amadeus.com"
ORIGIN = "FRA"
DESTINATION = "HND"
ADULTS = 2
STAY_DAYS = 23
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "preise.csv")

# Kandidaten für Hinflug-Daten: alle 5 Tage vom 01.02.2027 bis 10.03.2027.
# Rückflug = Hinflug + 23 Tage. Passe die Werte hier an, falls du engere
# oder weitere Zeitfenster testen willst.
START = date(2027, 2, 1)
END = date(2027, 3, 10)
STEP_DAYS = 5

TRAVEL_CLASSES = ["ECONOMY", "PREMIUM_ECONOMY"]


def get_departure_dates():
    dates = []
    d = START
    while d <= END:
        dates.append(d)
        d += timedelta(days=STEP_DAYS)
    return dates


def get_access_token():
    client_id = os.environ.get("AMADEUS_CLIENT_ID")
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("FEHLER: AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET nicht gesetzt.")
        sys.exit(1)

    resp = requests.post(
        f"{AMADEUS_BASE_URL}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def search_flights(token, departure_date, return_date, travel_class):
    params = {
        "originLocationCode": ORIGIN,
        "destinationLocationCode": DESTINATION,
        "departureDate": departure_date.isoformat(),
        "returnDate": return_date.isoformat(),
        "adults": ADULTS,
        "travelClass": travel_class,
        "nonStop": "true",
        "currencyCode": "EUR",
        "max": 5,
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers",
        params=params,
        headers=headers,
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"  Warnung: {resp.status_code} für {departure_date} {travel_class}: {resp.text[:200]}")
        return []
    return resp.json().get("data", [])


def extract_offers(offers, travel_class):
    """Nur Angebote behalten, deren tatsächliche Kabine passt, und die
    wichtigsten Felder herausziehen."""
    results = []
    for offer in offers:
        try:
            price = offer["price"]["total"]
            currency = offer["price"]["currency"]
            traveler_pricing = offer["travelerPricings"][0]
            cabin = traveler_pricing["fareDetailsBySegment"][0]["cabin"]
            if cabin != travel_class:
                continue
            carriers = set()
            for itinerary in offer["itineraries"]:
                for segment in itinerary["segments"]:
                    carriers.add(segment["carrierCode"])
            results.append(
                {
                    "price_total": price,
                    "currency": currency,
                    "cabin": cabin,
                    "airlines": "+".join(sorted(carriers)),
                }
            )
        except (KeyError, IndexError):
            continue
    return results


def ensure_csv_header():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "abfrage_datum",
                    "hinflug",
                    "rueckflug",
                    "klasse",
                    "preis_gesamt_eur",
                    "preis_pro_person_eur",
                    "airlines",
                ]
            )


def main():
    ensure_csv_header()
    token = get_access_token()
    heute = date.today().isoformat()

    zeilen = []
    for departure_date in get_departure_dates():
        return_date = departure_date + timedelta(days=STAY_DAYS)
        for travel_class in TRAVEL_CLASSES:
            print(f"Suche: {departure_date} -> {return_date} ({travel_class})")
            offers = search_flights(token, departure_date, return_date, travel_class)
            treffer = extract_offers(offers, travel_class)
            if not treffer:
                print("  Keine passenden Direktflug-Angebote gefunden.")
                continue
            bester = min(treffer, key=lambda x: float(x["price_total"]))
            preis_pp = round(float(bester["price_total"]) / ADULTS, 2)
            print(f"  Günstigstes Angebot: {bester['price_total']} {bester['currency']} "
                  f"gesamt ({preis_pp} pro Person, {bester['airlines']})")
            zeilen.append(
                [
                    heute,
                    departure_date.isoformat(),
                    return_date.isoformat(),
                    travel_class,
                    bester["price_total"],
                    preis_pp,
                    bester["airlines"],
                ]
            )

    if zeilen:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print(f"\n{len(zeilen)} neue Zeile(n) in {CSV_PATH} gespeichert.")
    else:
        print("\nKeine neuen Ergebnisse heute.")


if __name__ == "__main__":
    main()
