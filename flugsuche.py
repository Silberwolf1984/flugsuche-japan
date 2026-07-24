"""
Tägliche Preissuche für Flüge Frankfurt (FRA) -> Tokyo Haneda (HND)
für den Zeitraum Feb/März 2027 mit ca. 23 Tagen Aufenthalt.

Nutzt die Travelpayouts (Aviasales) Data API - "Latest Prices"-Endpunkt.
Das ist eine kostenlose, cache-basierte API (keine Live-Shopping-Abfrage):
Sie zeigt Preise, die aus echten Nutzersuchen bei Aviasales stammen.

WICHTIGE EINSCHRÄNKUNGEN (bitte im Hinterkopf behalten):
- Für weit in der Zukunft liegende Reisen (hier: 7+ Monate) kann die
  Trefferquote anfangs gering sein, da wenige Nutzer so früh suchen.
- Die API liefert praktisch nur Economy-Preise, keine separate
  Premium-Economy-Angabe.
- Es lässt sich kein exaktes Abflugdatum abfragen, nur ein Zeitraum
  (Monat) + eine gewünschte Reisedauer.
- Die Preise sind Cache-Preise, keine garantiert buchbaren Live-Tarife.
- Die API liefert keine Info, ob es sich um einen Direktflug handelt
  (kein "nonStop"-Filter) - das Skript kennzeichnet das entsprechend.

Benötigt eine Umgebungsvariable:
  TRAVELPAYOUTS_TOKEN

Schreibt/erweitert eine CSV-Datei unter data/preise.csv.
"""

import os
import csv
import sys
from datetime import date
import requests

API_URL = "https://api.travelpayouts.com/v2/prices/latest"
ORIGIN = "FRA"
DESTINATION = "HND"
CURRENCY = "eur"
TRIP_DURATION_MIN = 20
TRIP_DURATION_MAX = 26
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "preise.csv")

# Monate, für die wir Preise abfragen (Hinflug in diesem Monat)
MONTHS_TO_CHECK = ["2027-02-01", "2027-03-01"]


def get_token():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        print("FEHLER: TRAVELPAYOUTS_TOKEN nicht gesetzt.")
        sys.exit(1)
    return token


def search_prices(token, beginning_of_period):
    params = {
        "origin": ORIGIN,
        "destination": DESTINATION,
        "currency": CURRENCY,
        "period_type": "month",
        "beginning_of_period": beginning_of_period,
        "trip_duration_min": TRIP_DURATION_MIN,
        "trip_duration_max": TRIP_DURATION_MAX,
        "one_way": "false",
        "sorting": "price",
        "limit": 30,
        "page": 1,
    }
    headers = {"X-Access-Token": token}
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"  Warnung: {resp.status_code} für {beginning_of_period}: {resp.text[:200]}")
        return []
    payload = resp.json()
    if not payload.get("success", True):
        print(f"  API meldet Fehler: {payload}")
        return []
    return payload.get("data", [])


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
                    "reisedauer_tage",
                    "preis_pro_person_eur",
                    "airline",
                    "anzahl_zwischenstopps",
                    "hinweis",
                ]
            )


def main():
    ensure_csv_header()
    token = get_token()
    heute = date.today().isoformat()

    zeilen = []
    for monat in MONTHS_TO_CHECK:
        print(f"Suche Preise für Hinflüge ab {monat} ...")
        treffer = search_prices(token, monat)
        if not treffer:
            print("  Keine Treffer (evtl. noch keine Cache-Daten für diesen Zeitraum).")
            continue
        for eintrag in treffer:
            zeilen.append(
                [
                    heute,
                    eintrag.get("depart_date", ""),
                    eintrag.get("return_date", ""),
                    eintrag.get("duration", ""),
                    eintrag.get("value", ""),
                    eintrag.get("gate", ""),
                    eintrag.get("number_of_changes", ""),
                    "Cache-Preis, Economy, Direktflug nicht garantiert",
                ]
            )
            print(
                f"  {eintrag.get('depart_date')} -> {eintrag.get('return_date')}: "
                f"{eintrag.get('value')} EUR (pro Person, Cache-Preis, "
                f"{eintrag.get('number_of_changes', '?')} Zwischenstopp(s))"
            )

    if zeilen:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print(f"\n{len(zeilen)} neue Zeile(n) in {CSV_PATH} gespeichert.")
    else:
        print("\nKeine neuen Ergebnisse heute - das ist bei so weit in der Zukunft "
              "liegenden Daten normal und kann sich in den kommenden Wochen ändern.")


if __name__ == "__main__":
    main()
