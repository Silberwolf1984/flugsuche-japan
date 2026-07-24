"""
Gemeinsame Datenmodelle.

Diese Datei definiert die Objekte, mit denen alle anderen Module arbeiten.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Flight:
    """
    Repräsentiert einen Flug.
    """

    origin: str
    destination: str

    airline: str

    departure: datetime
    return_date: datetime

    price: int

    stops: int

    link: str = ""

    @property
    def is_direct(self) -> bool:
        return self.stops == 0

    @property
    def duration(self) -> int:
        return (self.return_date - self.departure).days
