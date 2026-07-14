"""Selection rules against the synthetic fixture CSV (FR-002)."""

import datetime as dt
from pathlib import Path

from recipients import due_today, load_recipients

FIXTURE = Path(__file__).parent / "fixtures" / "birthdays_fixture.csv"


def test_loads_only_active_complete_rows(caplog):
    people = load_recipients(FIXTURE)
    names = [person.firstname for person in people]
    # Ina (inactive), Emil (no email), Dora (incomplete date) and
    # Falk (unparsable year) must all be skipped.
    assert names == ["Anna", "Ben", "Greta"]


def test_unparsable_year_logs_warning(caplog):
    with caplog.at_level("WARNING"):
        load_recipients(FIXTURE)
    assert "Falk" in caplog.text


def test_fields_are_typed():
    anna = load_recipients(FIXTURE)[0]
    assert (anna.year, anna.month, anna.day) == (1950, 3, 5)
    assert anna.gender == "f"
    assert anna.email == "anna@example.org"


def test_due_today_matches_month_and_day():
    people = load_recipients(FIXTURE)
    due = due_today(people, dt.date(2026, 3, 5))
    assert [person.firstname for person in due] == ["Anna", "Ben"]


def test_due_today_empty_when_no_match():
    people = load_recipients(FIXTURE)
    assert due_today(people, dt.date(2026, 12, 24)) == []
