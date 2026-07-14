"""Recipient records and selection rules for the birthday CSV files."""

import csv
import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Recipient:
    firstname: str
    gender: str
    email: str
    year: int
    month: int
    day: int


def load_recipients(path: str | Path) -> list[Recipient]:
    """Read active, complete rows; skip the rest (warn on bad numbers)."""
    recipients = []
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            recipient = _parse_row(row)
            if recipient is not None:
                recipients.append(recipient)
    return recipients


def _parse_row(row: dict) -> Recipient | None:
    email = (row.get("email") or "").strip()
    date_fields = [(row.get(key) or "").strip()
                   for key in ("year", "month", "day")]
    active = (row.get("active") or "").strip()
    if active != "1" or not email or not all(date_fields):
        return None  # inactive or incomplete row: skip silently
    try:
        year, month, day = (int(value) for value in date_fields)
    except ValueError:
        log.warning("skipping row with unparsable birth date: %s",
                    row.get("firstname", "?"))
        return None
    return Recipient(
        firstname=(row.get("firstname") or "").strip(),
        gender=(row.get("gender") or "").strip(),
        email=email,
        year=year,
        month=month,
        day=day,
    )


def due_today(recipients: list[Recipient],
              today: dt.date) -> list[Recipient]:
    return [person for person in recipients
            if person.month == today.month and person.day == today.day]
