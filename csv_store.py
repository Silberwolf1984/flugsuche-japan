def last_price() -> int | None:
    """
    Liefert den zuletzt gespeicherten Preis.
    """

    history = load_history()

    if not history:
        return None

    try:
        return int(history[-1]["preis_pro_person_eur"])
    except (KeyError, ValueError):
        return None


def best_price() -> int | None:
    """
    Liefert den bisher günstigsten Preis.
    """

    history = load_history()

    prices = []

    for row in history:
        try:
            prices.append(int(row["preis_pro_person_eur"]))
        except (KeyError, ValueError):
            pass

    if not prices:
        return None

    return min(prices)
