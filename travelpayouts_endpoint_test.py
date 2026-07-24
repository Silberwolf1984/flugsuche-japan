import os
import requests

TOKEN = os.environ["TRAVELPAYOUTS_TOKEN"]

HEADERS = {
    "x-access-token": TOKEN
}

CURRENCY = "eur"
ORIGIN = "FRA"
DESTINATIONS = ["HND", "NRT", "TYO"]

TESTS = [
    (
        "cheap",
        "https://api.travelpayouts.com/v1/prices/cheap",
        {
            "depart_date": "2027-02",
            "return_date": "2027-03",
            "currency": CURRENCY,
        },
    ),
    (
        "calendar",
        "https://api.travelpayouts.com/v1/prices/calendar",
        {
            "depart_date": "2027-02",
            "return_date": "2027-03",
            "calendar_type": "departure_date",
            "trip_duration": 23,
            "currency": CURRENCY,
        },
    ),
    (
        "monthly",
        "https://api.travelpayouts.com/v1/prices/monthly",
        {
            "month": "2027-02",
            "currency": CURRENCY,
        },
    ),
]


def print_response(name, url, params):
    req = requests.Request(
        "GET",
        url,
        params=params,
        headers=HEADERS
    ).prepare()

    print("\n===================================================")
    print(f"ENDPUNKT : {name}")
    print(req.url)

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=30
    )

    print("HTTP:", response.status_code)

    try:
        payload = response.json()
    except Exception:
        print(response.text)
        return

    print("success:", payload.get("success"))

    data = payload.get("data")

    if isinstance(data, dict):
        print("Anzahl Keys:", len(data))
        print("Keys:", list(data.keys())[:20])

        if data:
            print("\nErste Daten:")
            first_key = next(iter(data))
            print(first_key)
            print(data[first_key])
    else:
        print(data)


def main():
    print("Travelpayouts API Vergleich")
    print("===========================")

    for destination in DESTINATIONS:
        print("\n")
        print("###################################################")
        print(f"{ORIGIN} -> {destination}")
        print("###################################################")

        for name, url, params in TESTS:
            p = params.copy()
            p["origin"] = ORIGIN
            p["destination"] = destination
            print_response(name, url, p)


if __name__ == "__main__":
    main()
