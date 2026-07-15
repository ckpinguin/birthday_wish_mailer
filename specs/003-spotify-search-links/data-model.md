# Data Model: Spotify Search Links

Two entities change; nothing is added. Field-level interface rules live in
[contracts/](contracts/).

## ChartEntry (field semantics change) — `charts.py`

| Field | Type | Change |
| ------------- | ------------- | ------------------------------------------------------------------------------------------------- |
| `title` | `str` | unchanged (scraped from Billboard) |
| `artist` | `str` | unchanged (scraped from Billboard) |
| `spotify_url` | `str \| None` | **semantics**: now a search-results URL built purely from `title` + `artist` (research R2), assigned to every fetched entry by `main.gather_chart_entries` (R1). Previously an exact track URL resolved via the blocked Web API, `None` on miss/failure. The `None` branch in `content.render_postscript` (item without link) remains as the degradation net (R4). |

The dataclass itself is untouched — only who writes the field and what the
value points to changes.

## AppConfig (shrinks) — `config.py`

| Field | Change |
| ----------------------- | ------------------------------------------------------------------------ |
| `spotify_client_id` | **removed** — nothing reads it after this feature (research R3) |
| `spotify_client_secret` | **removed** — same |
| all other fields | unchanged, including feature 002's `owner_recipient` |

`REQUIRED_KEYS` shrinks accordingly to: `MAILHOST`, `PORT`, `LOGIN`,
`PASSWORD`, `FROM_ADDR`, `SENDER`.

## Validation rules recap

1. A secrets file without any Spotify entry passes validation (FR-003).
2. A secrets file *with* leftover Spotify entries behaves identically —
   unknown keys were already ignored by `load_config` (FR-003).
3. Every `ChartEntry` handed to rendering carries a link built from its own
   `title` and `artist`, percent-encoded as one path segment (FR-001,
   FR-005).
4. Link construction is pure text work — no credential, no network call
   (FR-002); rendering still tolerates `spotify_url=None` (FR-006).
