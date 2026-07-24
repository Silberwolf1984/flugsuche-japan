"""
Zentrale Konfiguration für den Japan Flight Monitor.

Hier werden alle Einstellungen gepflegt, die sich im Laufe der Zeit
ändern können, ohne dass Logik angepasst werden muss.
"""

# ---------------------------------------------------------------------
# API
# ---------------------------------------------------------------------

API_URL = "https://api.travelpayouts.com/v1/prices/cheap"
CURRENCY = "eur"

# ---------------------------------------------------------------------
# Reise
# ---------------------------------------------------------------------

ORIGINS = [
    "FRA",
    "MUC",
    "DUS",
]

DESTINATION = "TYO"

# gewünschte Aufenthaltsdauer
STAY_DAYS_TARGET = 23
STAY_DAYS_TOLERANCE = 4

# Suchmonate
MONTH_COMBINATIONS = [
    ("2027-02", "2027-02"),
    ("2027-02", "2027-03"),
    ("2027-03", "2027-03"),
    ("2027-03", "2027-04"),
]

# ---------------------------------------------------------------------
# Airlines
# ---------------------------------------------------------------------

# Höhere Zahl = höhere Priorität.
#
# Reihenfolge:
# ANA / JAL
# Lufthansa
# Finnair
# KLM
# Air France
# Qatar
# Emirates
# Etihad
# Turkish

AIRLINE_PRIORITY = {
    "NH": 100,   # ANA
    "JL": 100,   # Japan Airlines

    "LH": 95,    # Lufthansa

    "AY": 90,    # Finnair

    "KL": 85,    # KLM
    "AF": 84,    # Air France

    "QR": 83,    # Qatar Airways
    "EK": 82,    # Emirates
    "EY": 81,    # Etihad Airways

    "TK": 80,    # Turkish Airlines
}

# Airlines, die grundsätzlich ignoriert werden.

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

# Airlines, die wir grundsätzlich akzeptieren,
# falls kein Direktflug vorhanden ist.

PREFERRED_AIRLINES = set(AIRLINE_PRIORITY.keys())

# ---------------------------------------------------------------------
# Diagnose
# ---------------------------------------------------------------------

# Testroute zur Überprüfung der API

SANITY_CHECK_ORIGINS = [
    "FRA",
    "MUC",
    "DUS",
]

SANITY_CHECK_DESTINATION = "BKK"

SANITY_CHECK_MONTH = (
    "2026-09",
    "2026-09",
)
