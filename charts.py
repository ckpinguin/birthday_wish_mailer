"""Fetch the Billboard Hot 100 top three for a given date."""

import datetime as dt
import logging
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

CHART_URL = "https://www.billboard.com/charts/hot-100/"
TOP_COUNT = 3
REQUEST_TIMEOUT = 30


class ChartsError(Exception):
    """Raised when the chart page cannot be fetched or parsed."""


@dataclass
class ChartEntry:
    title: str
    artist: str
    spotify_url: str | None = None


def fetch_top_three(date: dt.date) -> list[ChartEntry]:
    url = f"{CHART_URL}{date.isoformat()}"
    log.info("fetching charts from %s", url)
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ChartsError(f"could not fetch {url}: {exc}") from exc
    return parse_top_three(response.text)


def parse_top_three(html: str) -> list[ChartEntry]:
    soup = BeautifulSoup(html, "html.parser")
    titles = [tag.get_text(strip=True)
              for tag in soup.select("li h3.c-title")]
    artists = [tag.get_text(strip=True) for tag in soup.select(
        "li.o-chart-results-list__item span.c-label.a-no-trucate")]
    entries = [ChartEntry(title=title, artist=artist)
               for title, artist in zip(titles, artists)]
    if not entries:
        raise ChartsError("no chart entries found - layout changed?")
    return entries[:TOP_COUNT]
