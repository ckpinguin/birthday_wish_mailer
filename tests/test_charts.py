"""Chart page parsing against a saved fixture (offline)."""

from pathlib import Path

import pytest

from charts import ChartsError, parse_top_three

FIXTURE = Path(__file__).parent / "fixtures" / "billboard_sample.html"


def test_parses_top_three_in_order():
    entries = parse_top_three(FIXTURE.read_text(encoding="utf-8"))
    assert [(e.title, e.artist) for e in entries] == [
        ("First Song", "First Artist"),
        ("Second Song", "Second Artist"),
        ("Third Song", "Third Artist"),
    ]


def test_truncates_to_three():
    entries = parse_top_three(FIXTURE.read_text(encoding="utf-8"))
    assert len(entries) == 3  # fixture contains four chart items


def test_garbage_html_raises():
    with pytest.raises(ChartsError):
        parse_top_three("<html><body><p>nothing here</p></body></html>")


def test_empty_html_raises():
    with pytest.raises(ChartsError):
        parse_top_three("")
