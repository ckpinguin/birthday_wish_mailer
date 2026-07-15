"""Build Spotify search links for chart songs (no API, no credentials).

Spotify's February 2026 policy blocks Web API access for developer
accounts without Premium, so exact track lookups are no longer available;
a search-results link needs neither an account nor a network call.
"""

from urllib.parse import quote


def search_url(title: str, artist: str) -> str:
    query = quote(f"{title} {artist}", safe="")
    return f"https://open.spotify.com/search/{query}"
