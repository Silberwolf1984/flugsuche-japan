"""
config.py

Zentrale Konfiguration des Japan Flight Monitors.
Hier befinden sich alle Einstellungen, die ohne Änderungen am Programmcode
angepasst werden können.
"""

# ---------------------------------------------------------------------
# API
# ---------------------------------------------------------------------

API_URL = "https://api.travelpayouts.com/v1/prices/cheap"
CURRENCY = "eur"

# ---------------------------------------------------------------------
# Reise
# ---------------------------------------------------------------------

# Abflughäfen
ORIGINS = [
    "FRA",
    "MUC",
    "DUS",
]

# Ziel
DESTINATION = "TYO"

# Gewünschte Aufenthaltsdauer
STAY_DAYS_TARGET = 21
STAY_DAYS_TOLERANCE = 3

# Suchzeiträume
MONTH_COMBINATIONS = [
    ("2027-02", "2027-02"),
    ("2027-02", "2027-03"),
    ("2027-03", "2027-03"),
    ("2027-03", "2027-04"),
]

# ---------------------------------------------------------------------
# Airline-Ranking
# ---------------------------------------------------------------------

# Höherer Wert = höhere Priorität
#
# Dieses Ranking wird vom Ranking-Modul verwendet.
# Alle nicht aufgeführten Airlines erhalten automatisch Priorität 0.

AIRLINE_PRIORITY = {

    # Japan
    "NH": 100,   # ANA
    "JL": 100,   # Japan Airlines

    # Deutschland
    "LH": 95,    # Lufthansa

    # Europa
    "AY": 90,    # Finnair
    "KL": 85,    # KLM
    "AF": 84,    # Air France

    # Naher Osten
    "QR": 83,    # Qatar Airways
    "EK": 82,    # Emirates
    "EY": 81,    # Etihad Airways
    "TK": 80,    # Turkish Airlines
}

# ---------------------------------------------------------------------
# Airlines ausschließen
# ---------------------------------------------------------------------

# Diese Airlines werden grundsätzlich ignoriert.

EXCLUDED_AIRLINES = {
    "CA",   # Air China
    "CZ",   # China Southern
    "MU",   # China Eastern
    "MF",   # XiamenAir
    "HU",   # Hainan Airlines
    "3U",   # Sichuan Airlines
    "9C",   # Spring Airlines
    "HO",   # Juneyao Airlines
    "GS",   # Tianjin Airlines
    "SC",   # Shandong Airlines
    "ZH",   # Shenzhen Airlines
}

# ---------------------------------------------------------------------
# Dateien
# ---------------------------------------------------------------------

CSV_PATH = "flugpreise.csv"

# ---------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------

DEBUG = False
