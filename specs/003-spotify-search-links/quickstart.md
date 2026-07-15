# Quickstart: Validating Spotify Search Links

Run in order after implementation. Everything except scenario 4's clicks is
offline or test-mode-only. Contracts: [contracts/](contracts/); field
rules: [data-model.md](data-model.md).

## Prerequisites

- Working `.secret.json` (feature 002 state, incl. `OWNER_RECIPIENT`)
- `TEST_birthdays.csv` with at least one active row whose month/day match
  today **and whose birth year is 1958 or later** (so a chart P.S. is
  generated)
- Dev venv with `requirements-dev.txt` installed

## 1. Offline checks (no network, no mail)

```sh
.venv/bin/python -m pytest
.venv/bin/python -m flake8 .
```

**Expected**: all tests pass, including the new link-encoding tests
(spaces, `&`, `/`, umlauts, apostrophes) and the updated config tests;
flake8 silent.

## 2. Spot-check link quality (SC-002, no mail involved)

Generate links for a handful of historical chart songs and open a few:

```sh
.venv/bin/python -c "
from spotify_links import search_url
for t, a in [('Hey Jude', 'The Beatles'), ('Bad Guy', 'Billie Eilish'),
             ('Rock Around The Clock', 'Bill Haley & His Comets')]:
    print(search_url(t, a))
"
```

**Expected**: three well-formed `https://open.spotify.com/search/…` URLs
with no raw spaces/`&`; opened in a browser (even logged out), the intended
song is visible in the results. For the formal SC-002 sample, repeat with
10 songs from past birthday runs — ≥ 9 must show the song.

## 3. Config without Spotify entries (FR-003)

Remove `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from `.secret.json`
(or leave them — test both if you like), then:

```sh
./run.sh --test
```

**Expected**: run completes with no configuration error and no Spotify
mention in the logs; per-send log lines (feature 002 format) appear as
before.

## 4. Test send — email inspection (Principle III gate)

In the mail received from scenario 3's run:

- P.S. block looks exactly as before (intro line, 3 songs, YouTube hint)
- each song is a link; clicking it opens Spotify search results showing
  that song
- routing block and subject (feature 002) unchanged

## 5. Regression sweep

```sh
.venv/bin/python -m pytest && .venv/bin/python -m flake8 .
```

**Expected**: clean, plus a quick skim of `git diff` confirming
`charts.py` and `content.py` are untouched and `requirements.txt` is
unchanged. Then deploy and watch the next timer run per the feature 002
quickstart (scenario 6).
