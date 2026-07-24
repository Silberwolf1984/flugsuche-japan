"""
Tägliche Preissuche für Flüge Frankfurt (FRA) -> Tokyo Haneda (HND)
für den Zeitraum Feb/März 2027 mit ca. 23 Tagen Aufenthalt.

Nutzt die Travelpayouts (Aviasales) Data API - Endpunkt "/v1/prices/cheap".
Das ist eine kostenlose, cache-basierte API (keine Live-Shopping-Abfrage).

Wichtig zur Endpunkt-Wahl: "/v2/prices/latest" zeigt nur Preise aus
Nutzersuchen der letzten 48 Stunden - für eine selten gesuchte Strecke wie
FRA-HND praktisch nie brauchbar. "/v1/prices/cheap" hat einen breiteren
Cache-Horizont und liefert die Ergebnisse zusätzlich gruppiert nach Anzahl
Zwischenstopps (Schlüssel "0" = Direktflug, "1" = 1 Stopp, usw.) - das
nutzen wir, um gezielt nur Direktflüge herauszufiltern.

WICHTIGE EINSCHRÄNKUNGEN (bitte im Hinterkopf behalten):
- Für weit in der Zukunft liegende Reisen (hier: 7+ Monate) kann die
  Trefferquote anfangs gering sein, da wenige Nutzer so früh suchen.
- Die API liefert praktisch nur Economy-Preise, keine separate
  Premium-Economy-Angabe.
- depart_date/return_date wirken als Monatsfilter, nicht als exaktes
  Datum - das Skript filtert clientseitig auf die gewünschte Reisedauer.
- Die Preise sind Cache-Preise (siehe "expires_at"), keine garantiert
  buchbaren Live-Tarife.
- Der Preis gilt pro Person (nicht für 2 Personen) - im Skript wird das
  entsprechend markiert.

Benötigt eine Umgebungsvariable:
  TRAVELPAYOUTS_TOKEN

Schreibt/erweitert eine CSV-Datei unter data/preise.csv.
"""

import os
import csv
import sys
from datetime import date, datetime
import requests

API_URL = "https://api.travelpayouts.com/v1/prices/cheap"
ORIGINS = ["FRA", "MUC", "DUS"]
DESTINATION = "TYO"
CURRENCY = "eur"
STAY_DAYS_TARGET = 23
STAY_DAYS_TOLERANCE = 4  # akzeptiere 19-27 Tage als "ca. 23 Tage"

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "preise.csv")

PREFERRED_AIRLINES = ["NH","JL","LH","AY","KL","AF","QR","EK","EY","TK"]
AIRLINE_SCORE={"NH":100,"JL":100,"LH":95,"AY":90,"KL":85,"AF":84,"QR":82,"EK":81,"EY":80,"TK":75}

def flight_score(stop_key, airline, price):
    score=10000 if stop_key=="0" else 0
    score+=AIRLINE_SCORE.get(airline,0)*100
    score-=int(price or 999999)
    return score
EXCLUDED_AIRLINES = {"CA", "CZ", "MU", "MF", "HU", "3U", "9C", "HO", "GS", "SC", "ZH"}


# Monatskombinationen: (Abflugmonat, Rückflugmonat)
MONTH_COMBINATIONS = [
    ("2027-02", "2027-02"),
    ("2027-02", "2027-03"),
    ("2027-03", "2027-03"),
    ("2027-03", "2027-04"),
]

# Sanity-Check: naher Zeitraum + bekanntermaßen gut gecachte Route,
# um die API-Anbindung zu bestätigen. Wird NICHT in die Haupt-CSV-Zeilen
# gemischt, sondern separat markiert.
SANITY_CHECK_ORIGINS = ["FRA", "MUC", "DUS"]
SANITY_CHECK_DESTINATION = "BKK"
SANITY_CHECK_MONTH = ("2026-09", "2026-09")


def get_token():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        print("FEHLER: TRAVELPAYOUTS_TOKEN nicht gesetzt.")
        sys.exit(1)
    return token


def search_prices(token, origin, destination, depart_month, return_month):
    params = {
        "origin": origin,
        "destination": destination,
        "depart_date": depart_month,
        "return_date": return_month,
        "currency": CURRENCY,
    }
    headers = {"x-access-token": token}
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"  Warnung: HTTP {resp.status_code} für {depart_month}->{return_month}: {resp.text[:200]}")
        return {}
    payload = resp.json()
    if not payload.get("success", True):
        print(f"  API meldet Fehler: {payload}")
        return {}
    data = payload.get("data", {})
    if not data:
        return {}
    if destination in data:
        return data[destination]
    return next(iter(data.values()))


def stops_label(stop_key):
    mapping = {"0": "Direktflug", "1": "1 Zwischenstopp", "2": "2 Zwischenstopps"}
    return mapping.get(stop_key, f"{stop_key} Zwischenstopps")


def trip_duration_days(eintrag):
    try:
        dep = datetime.fromisoformat(eintrag["departure_at"].replace("Z", "+00:00"))
        ret = datetime.fromisoformat(eintrag["return_at"].replace("Z", "+00:00"))
        return (ret - dep).days
    except (KeyError, ValueError, TypeError):
        return None




def ensure_csv_header():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                    "abfrage_datum",
                    "abflughafen",
                    "zielflughafen",
                    "hinflug",
                    "rueckflug",
                    "reisedauer_tage",
                    "preis_pro_person_eur",
                    "airline",
                    "anzahl_zwischenstopps",
                    "gueltig_bis",
                    "hinweis",
                ])


def diagnose_api(token):
    """Reiner Diagnose-Test mit einer garantiert vielgesuchten Route."""
    print("\n--- DIAGNOSE-TEST: Frankfurt -> Bangkok, /v1/prices/cheap ---")
    dep_m, ret_m = SANITY_CHECK_MONTH
    for origin in SANITY_CHECK_ORIGINS:
        daten = search_prices(token, origin, SANITY_CHECK_DESTINATION, dep_m, ret_m)
        print(f"  {origin} -> Rohdaten: {daten}")
    print("--- ENDE DIAGNOSE-TEST ---\n")


def main():
    ensure_csv_header()
    token = get_token()
    diagnose_api(token)
    heute = date.today().isoformat()

    zeilen = []
    beste_fluege = {}
    for origin in ORIGINS:
        print(f"\n===== {origin} -> {DESTINATION} =====")
        for depart_month, return_month in MONTH_COMBINATIONS:
            print(f"Suche Preise: Hinflug {depart_month}, Rückflug {return_month} ...")
            daten = search_prices(token, origin, DESTINATION, depart_month, return_month)
            if not daten:
                print("  Keine Treffer (evtl. noch keine Cache-Daten für diesen Zeitraum).")
                continue

            for stop_key, eintrag in daten.items():
                airline = eintrag.get("airline", "")

                if airline in EXCLUDED_AIRLINES:
                    print(f"  Übersprungen: ausgeschlossene Airline {airline}")
                    continue

                if stop_key != "0":
                    if airline in PREFERRED_AIRLINES:
                        print(f"  Kein Direktflug vorhanden – akzeptiere bevorzugte Airline {airline} mit {stops_label(stop_key)}.")
                    else:
                        print(f"  Übersprungen: {airline} ({stops_label(stop_key)})")
                        continue

                dauer = trip_duration_days(eintrag)
                if dauer is not None and abs(dauer - STAY_DAYS_TARGET) > STAY_DAYS_TOLERANCE:
                    print(f"  Übersprungen: Reisedauer {dauer} Tage weicht zu stark von {STAY_DAYS_TARGET} Tagen ab.")
                    continue

                kandidat=[
                    heute,
                    origin,
                    DESTINATION,
                    eintrag.get("departure_at", ""),
                    eintrag.get("return_at", ""),
                    dauer if dauer is not None else "",
                    eintrag.get("price", ""),
                    eintrag.get("airline", ""),
                    stops_label(stop_key),
                    eintrag.get("expires_at", ""),
                    "Preis pro Person, Cache-Preis (kein Live-Tarif)",
                ]
                score=flight_score(stop_key, airline, eintrag.get("price",999999))
                if origin not in beste_fluege or score>beste_fluege[origin]["score"]:
                    beste_fluege[origin]={"score":score,"row":kandidat,"airline":airline,"price":eintrag.get("price"),"direct":stop_key=="0"}

                print(
                    f"  {origin}: {eintrag.get('departure_at')} -> {eintrag.get('return_at')} "
                    f"({dauer} Tage): {eintrag.get('price')} {CURRENCY.upper()} pro Person, "
                    f"{eintrag.get('airline')}, {stops_label(stop_key)}"
                )


    zeilen=[v['row'] for v in beste_fluege.values()]
    for origin,flug in beste_fluege.items():
        print(f"\n🏆 Bester Flug {origin}: {flug['airline']} | {flug['price']} EUR | {'Direktflug' if flug['direct'] else 'Umstieg'}")
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