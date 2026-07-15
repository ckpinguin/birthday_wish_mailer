"""Spotify search link construction: pure text, no network, no credentials."""

from spotify_links import search_url


def test_simple_title_and_artist():
    url = search_url("Hey Jude", "The Beatles")
    assert url == "https://open.spotify.com/search/Hey%20Jude%20The%20Beatles"


def test_ampersand_in_artist_is_encoded():
    url = search_url("Song", "X & Y")
    assert "&" not in url.removeprefix("https://open.spotify.com/search/")
    assert "%26" in url


def test_slash_in_title_is_encoded():
    url = search_url("AM/FM", "Artist")
    after_prefix = url.removeprefix("https://open.spotify.com/search/")
    assert "/" not in after_prefix
    assert "%2F" in url


def test_apostrophe_is_encoded():
    url = search_url("Ain't No Sunshine", "Bill Withers")
    assert "'" not in url
    assert "%27" in url


def test_non_ascii_characters_are_encoded():
    url = search_url("Röyksopp's Night Out", "Röyksopp")
    assert "ö" not in url
    assert url.startswith("https://open.spotify.com/search/")


def test_result_is_single_path_segment():
    url = search_url("Long Title With Many Words", "An Artist Name Too")
    after_prefix = url.removeprefix("https://open.spotify.com/search/")
    assert "/" not in after_prefix
    assert " " not in after_prefix
