"""Find Spotify track links via the Web API (client credentials)."""

import logging

import requests

log = logging.getLogger(__name__)

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
REQUEST_TIMEOUT = 30


class SpotifyError(Exception):
    """Raised when a Spotify API call fails."""


def get_token(client_id: str, client_secret: str) -> str:
    try:
        response = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise SpotifyError(f"could not get Spotify token: {exc}") from exc


def find_track_url(token: str, title: str, artist: str) -> str | None:
    """Return the Spotify URL of the best match, or None if no hit."""
    try:
        response = requests.get(
            SEARCH_URL,
            params={"q": f"track:{title} artist:{artist}",
                    "type": "track", "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        items = response.json()["tracks"]["items"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise SpotifyError(f"search for '{title}' failed: {exc}") from exc
    if not items:
        return None
    return items[0]["external_urls"]["spotify"]
