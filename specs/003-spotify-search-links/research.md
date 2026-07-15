# Research: Spotify Search Links

Decisions R1–R6, referenced from plan.md, data-model.md, and the contracts.
Background fact driving the feature: since Spotify's February 2026
Development Mode changes (announced 2026-02-06, enforced 2026-02-11 for new
client IDs and 2026-03-09 for existing ones), Web API access requires the
developer account to hold a Premium subscription. The owner has a free
account, so the app's client-credentials lookups are hard-blocked.

## R1: Where the search link is built

- **Decision**: `spotify_links.py` stays as the module but shrinks to one
  pure function, `search_url(title, artist) -> str`. `main.gather_chart_entries`
  assigns it to `entry.spotify_url` for every fetched chart entry. All API
  machinery (`get_token`, `find_track_url`, `SpotifyError`, `requests`
  usage) is deleted.
- **Rationale**: Keeps the one-responsibility-per-file layout ("everything
  Spotify" lives where it always did), keeps `content.py` provider-agnostic,
  and makes the diff minimal: `charts.py` and `content.py` don't change at
  all. Deletion over dormancy follows the spec assumption and Principle I —
  the policy is not expected to reverse for hobby-scale apps, and the git
  history preserves the old code if it ever does.
- **Alternatives considered**: building the link inside `charts.py`
  (rejected: charts module is about Billboard scraping, and `ChartEntry`
  would gain provider knowledge); building it in `content.py` during
  rendering (rejected: rendering already has one job, and the URL is data,
  not presentation); keeping the API path behind a config switch (rejected:
  dead code contradicts Principle I, and nobody can exercise it without
  Premium).

## R2: Link format and encoding

- **Decision**: `https://open.spotify.com/search/` + `urllib.parse.quote`
  of `"{title} {artist}"` with `safe=""`, so spaces become `%20` and
  path-hostile characters (`&`, `/`, `?`, `#`, umlauts, apostrophes) are
  percent-encoded into a single valid path segment.
- **Rationale**: `open.spotify.com/search/<query>` is Spotify's public web
  player search route — viewable without login, no API involved. Percent-
  encoding with `safe=""` guarantees the query survives as one path segment
  (a raw `/` in a title like "AM/FM" would otherwise split the path) and
  produces an href with no raw `&`, so it can be inserted into the existing
  HTML template untouched. stdlib `urllib.parse` means zero new
  dependencies.
- **Alternatives considered**: `?q=` query-parameter form (rejected: the
  web player's canonical search route is path-based); leaving spaces as
  `+` via `quote_plus` (rejected: `+` is only space-safe in query strings,
  not path segments); YouTube or iTunes links (rejected in spec: user chose
  Spotify search links, and the template's YouTube hint already covers
  non-Spotify readers).

## R3: Configuration surface

- **Decision**: Remove `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from
  `REQUIRED_KEYS` **and** drop the `spotify_client_id`/`spotify_client_secret`
  fields from `AppConfig` entirely. `load_config` already ignores unknown
  keys, so stale entries in existing `.secret.json` files are harmless
  (FR-003, acceptance 2.2).
- **Rationale**: Optional-but-unused fields are exactly the speculative
  clutter Principle I forbids. Nothing reads them after this feature.
- **Alternatives considered**: keeping the fields optional "in case the API
  comes back" (rejected: YAGNI; restoring two dataclass fields is a
  one-minute change if ever needed).

## R4: Failure handling for link building

- **Decision**: No try/except around link construction. FR-006 is satisfied
  structurally: `search_url` is a pure stdlib string operation on values
  that are always `str` (scraped text), with no I/O and no realistic raise
  path. The existing `spotify_url=None → render without link` branch in
  `render_postscript` stays as the safety net for any entry that somehow
  lacks a link.
- **Rationale**: Guarding an operation that cannot fail is noise
  (Principle I). The degradation ladder that matters — chart fetch fails →
  no P.S.; link missing → plain list item — is untouched (Principle IV).
- **Alternatives considered**: wrapping each link assignment in try/except
  (rejected: unreachable handler, misleads readers into thinking this is a
  network call).

## R5: Logging

- **Decision**: Delete the per-song lookup log lines and the token-failure
  warning from `gather_chart_entries` (there are no lookups anymore). Chart
  fetch logging and per-send logging (feature 002 contract) are unchanged.
- **Rationale**: Principle V demands logs that reconstruct what happened;
  logging "spotify link ok" for a string concatenation would fabricate an
  event that never occurred. The remaining logs still tell the whole story:
  chart lookup outcome + send outcome.
- **Alternatives considered**: keeping a one-line "search links attached"
  info log (rejected: it can never vary, so it carries no information).

## R6: Knock-on simplification in main.py

- **Decision**: `gather_chart_entries(person, config)` loses its `config`
  parameter — the only thing it used config for was Spotify credentials.
  `send_to_person` passes one argument fewer.
- **Rationale**: Honest signatures; the function is now Billboard-only plus
  link decoration.
- **Alternatives considered**: keeping the parameter for signature
  stability (rejected: nothing else consumes it; internal function).

## Constitution note (for the gate)

Constitution v1.0.1's Technology & Data Constraints names "requests against
the Spotify Web API for song links" as part of the core stack and states
"Replacements require justification under Principle I." Justification: the
API is externally blocked for the owner's account tier (February 2026
policy), and the replacement deletes a network integration, an OAuth token
flow, an exception class, and two secrets in favor of one pure function.
After implementation, the constitution should get a PATCH amendment
(via `/speckit-constitution`) updating that clause — outside this plan's
scope, flagged in plan.md.
