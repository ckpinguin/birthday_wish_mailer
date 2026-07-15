# Implementation Plan: Spotify Search Links

**Branch**: `003-spotify-search-links` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-spotify-search-links/spec.md`

## Summary

Spotify's February 2026 policy blocks Web API access for non-Premium
developer accounts, so the app's exact-track lookups fail and emails go out
with unlinked song lists. Replace the whole lookup (OAuth token flow +
search endpoint + two secrets) with pure text construction: every chart
song links to `https://open.spotify.com/search/<percent-encoded "title
artist">`. `spotify_links.py` shrinks to one function, `SPOTIFY_CLIENT_ID`/
`SPOTIFY_CLIENT_SECRET` leave `AppConfig` and the required keys, and
`gather_chart_entries` drops its now-unused config parameter. The P.S.
block's appearance, the degradation ladder, and feature 002's review
routing are untouched.

## Technical Context

**Language/Version**: Python ≥ 3.12 (unchanged)

**Primary Dependencies**: unchanged — runtime `requests` (still used by
`charts.py` for Billboard) + `beautifulsoup4`; the new link builder is
stdlib `urllib.parse` only; dev-only `pytest`, `flake8`

**Storage**: local files — `.secret.json` *loses* two required keys; CSV,
templates, images unchanged

**Testing**: pytest (offline: URL encoding cases, config without Spotify
keys) + flake8; end-to-end via `./run.sh --test` per
[quickstart.md](quickstart.md)

**Target Platform**: Linux homeserver (systemd timer, journald logs);
macOS for development

**Project Type**: single CLI application, flat module layout (unchanged)

**Performance Goals**: N/A — link building is string formatting; the run
gets *faster* (up to 4 network calls per birthday person removed)

**Constraints**: P.S. block markup byte-identical except `href` values
(FR-004); no new failure mode may abort a send (FR-006); secrets file
without Spotify entries must validate (FR-003); tests stay offline

**Scale/Scope**: 3 modules touched (`spotify_links.py` rewritten ~50→~15
LOC, `config.py` −4 lines, `main.py` −20 lines), 2 test files touched, 1
new test file; net LOC decrease

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Pre-research | Post-design |
| --- | ----------- | -------------- | ------------- |
| I | Simplicity First | PASS — feature *removes* an integration: OAuth flow, exception class, 2 secrets → one pure function | PASS — no new deps (stdlib `urllib.parse`); dead code deleted, not flagged off (R1, R3); `gather_chart_entries` signature shrinks (R6) |
| II | Secrets & personal data out of repo | PASS — two secrets fewer to protect; nothing new committed | PASS — contracts/README use example songs only; leftover keys ignored, no forced migration (config-delta.md) |
| III | Test mode before real sends | PASS — email content changes (hrefs), so `--test` verification is mandatory | PASS — quickstart 3–4 gate deployment; link quality spot-check runs without sending anything (quickstart 2) |
| IV | Graceful degradation of enrichment | PASS — degradation ladder preserved; link step can no longer fail at all | PASS — chart-failure → no P.S. unchanged; `None`-link rendering branch kept as net (R4, email-links.md) |
| V | Observable unattended runs | PASS — logs must stay truthful once lookups disappear | PASS — per-song lookup logs deleted with the lookups; chart + per-send logs unchanged (R5, email-links.md log delta) |

**Technology-constraint note**: constitution v1.0.1 names "requests against
the Spotify Web API for song links" in Technology & Data Constraints, with
replacements allowed "with justification under Principle I". Justification
(research, Constitution note): the API is externally blocked for the
owner's account tier, and the replacement deletes network code and secrets.
Follow-up after implementation: PATCH amendment via `/speckit-constitution`
to update that clause. Not a violation → Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-spotify-search-links/
├── plan.md              # This file
├── research.md          # Phase 0: decisions R1–R6 + constitution note
├── data-model.md        # Phase 1: ChartEntry semantics, AppConfig shrink
├── quickstart.md        # Phase 1: validation scenarios 1–5
├── contracts/
│   ├── email-links.md   # link format, encoding rules, degradation ladder, log delta
│   └── config-delta.md  # .secret.json required-keys delta, startup behavior, docs
└── tasks.md             # Phase 2 (/speckit-tasks — not created by /speckit-plan)
```

### Source Code (repository root)

```text
spotify_links.py         # REWRITTEN: single pure search_url(title, artist) helper
                         #            (urllib.parse.quote, safe=""); get_token,
                         #            find_track_url, SpotifyError, requests import deleted (R1, R2)
config.py                # MODIFIED: SPOTIFY_CLIENT_ID/SECRET out of REQUIRED_KEYS;
                         #           spotify_client_id/secret fields removed from AppConfig (R3)
main.py                  # MODIFIED: gather_chart_entries(person) — config param dropped (R6);
                         #           assigns search_url to every entry; token/per-song
                         #           lookup logging removed (R5); send_to_person call updated

tests/
├── test_spotify_links.py  # NEW: encoding cases — spaces, &, /, umlauts, apostrophes,
│                          #      long strings; result is one https://open.spotify.com/search/ URL
├── test_config.py         # MODIFIED: VALID_DATA loses Spotify keys; add leftover-keys-ignored case
└── test_content.py        # unchanged (P.S. markup untouched — that's the point)

README.md                # MODIFIED: drop Spotify keys from required list and the
                         #           developer-app instructions; note links go to search results

charts.py                # unchanged (ChartEntry dataclass as-is)
content.py               # unchanged (render_postscript already handles link/no-link)
requirements.txt         # unchanged (requests still needed for Billboard)
```

**Structure Decision**: The Spotify module keeps its name and single
responsibility but flips from "integration" to "pure helper" (research R1).
`charts.py` and `content.py` staying untouched is the design's proof that
the P.S. appearance can't regress (FR-004): the only writer of
`spotify_url` changes, nothing that reads it does. Net code delta is
negative — the feature deletes more than it adds.

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
