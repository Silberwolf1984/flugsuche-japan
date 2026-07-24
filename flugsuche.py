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
BUSINESS_API_URL = "https://api.travelpayouts.com/v2/prices/latest"
ORIGINS = [
    "FRA",  # Frankfurt
    "MUC",  # München
    "DUS",  # Düsseldorf
]
DESTINATION = "HND"
CURRENCY = "eur"
STAY_DAYS_TARGET = 23
STAY_DAYS_TOLERANCE = 4  # akzeptiere 19-27 Tage als "ca. 23 Tage"
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "preise.csv")

# Business Class: eigener, optionaler Suchdurchlauf. Nutzt zwangsläufig
# "/v2/prices/latest" (einziger Endpunkt mit trip_class-Parameter), der
# nur Preise aus Nutzersuchen der letzten 48 Stunden zeigt - bei Business
# Class + Nischenroute ist die Trefferwahrscheinlichkeit gering, schadet
# aber nicht, es trotzdem regelmäßig zu versuchen.
BUSINESS_MONTHS = ["2027-02-01", "2027-03-01"]

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
SANITY_CHECK_ORIGIN = "FRA"
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
    # Struktur: data -> { "HND": { "0": {...}, "1": {...} } }
    return payload.get("data", {}).get(destination, {})


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


def search_business_prices(token, beginning_of_period):
    params = {
        "origin": ORIGIN,
        "destination": DESTINATION,
        "currency": CURRENCY,
        "period_type": "month",
        "beginning_of_period": beginning_of_period,
        "trip_class": 1,  # 1 = Business Class
        "one_way": "false",
        "sorting": "price",
        "limit": 30,
        "page": 1,
    }
    headers = {"x-access-token": token}
    resp = requests.get(BUSINESS_API_URL, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"  Warnung: HTTP {resp.status_code} für {beginning_of_period}: {resp.text[:200]}")
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
                    "verbindung",
                    "gueltig_bis",
                    "hinweis",
                ]
            )


def diagnose_api(token):
    """Reiner Diagnose-Test mit einer garantiert vielgesuchten Route,
    um zu prüfen, ob die API grundsätzlich Daten liefert.
    Schreibt NICHTS in die CSV, nur Log-Ausgabe."""
    print("\n--- DIAGNOSE-TEST: Frankfurt -> Bangkok, /v1/prices/cheap ---")
    dep_m, ret_m = SANITY_CHECK_MONTH
    daten = search_prices(token, SANITY_CHECK_ORIGIN, SANITY_CHECK_DESTINATION, dep_m, ret_m)
    print(f"  Rohdaten: {daten}")
    print("--- ENDE DIAGNOSE-TEST ---\n")


def main():
    ensure_csv_header()
    token = get_token()
    diagnose_api(token)
    heute = date.today().isoformat()

    zeilen = []
    for depart_month, return_month in MONTH_COMBINATIONS:
        print(f"Suche Preise: Hinflug {depart_month}, Rückflug {return_month} ...")
        daten = search_prices(token, ORIGIN, DESTINATION, depart_month, return_month)
        if not daten:
            print("  Keine Treffer (evtl. noch keine Cache-Daten für diesen Zeitraum).")
            continue
        for stop_key, eintrag in daten.items():
            dauer = trip_duration_days(eintrag)
            if dauer is not None and abs(dauer - STAY_DAYS_TARGET) > STAY_DAYS_TOLERANCE:
                print(f"  Übersprungen: Reisedauer {dauer} Tage weicht zu stark von {STAY_DAYS_TARGET} Tagen ab.")
                continue
            zeilen.append(
                [
                    heute,
                    eintrag.get("departure_at", ""),
                    eintrag.get("return_at", ""),
                    dauer if dauer is not None else "",
                    eintrag.get("price", ""),
                    eintrag.get("airline", ""),
                    stops_label(stop_key),
                    eintrag.get("expires_at", ""),
                    "Preis pro Person, Cache-Preis (kein Live-Tarif)",
                ]
            )
            print(
                f"  {eintrag.get('departure_at')} -> {eintrag.get('return_at')} "
                f"({dauer} Tage): {eintrag.get('price')} {CURRENCY.upper()} pro Person, "
                f"{eintrag.get('airline')}, {stops_label(stop_key)}"
            )

    # --- Zusätzlicher, optionaler Durchlauf: Business Class ---
    # Eigener Endpunkt mit anderem Cache-Verhalten (nur letzte 48h),
    # daher bewusst getrennt von der Economy-Hauptsuche oben.
    for monat in BUSINESS_MONTHS:
        print(f"Suche Business-Class-Preise für Hinflüge ab {monat} ...")
        treffer = search_business_prices(token, monat)
        if not treffer:
            print("  Keine Treffer (Business Class + Nischenroute -> selten Cache-Daten vorhanden).")
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
                    "Business Class",
                    "",
                    "BUSINESS CLASS - Cache nur letzte 48h, Direktflug nicht garantiert",
                ]
            )
            print(
                f"  BUSINESS CLASS: {eintrag.get('depart_date')} -> {eintrag.get('return_date')}: "
                f"{eintrag.get('value')} {CURRENCY.upper()} pro Person ({eintrag.get('gate')})"
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
