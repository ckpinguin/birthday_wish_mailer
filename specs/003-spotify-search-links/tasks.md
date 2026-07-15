# Tasks: Spotify Search Links

**Input**: Design documents from `/specs/003-spotify-search-links/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R6), data-model.md, contracts/, quickstart.md

**Tests**: Included — plan.md's Technical Context mandates offline pytest coverage for URL encoding and the shrunk config, and the constitution requires flake8-clean, offline-testable results.

**Organization**: Tasks are grouped by user story so each story is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)

## Path Conventions

Flat single-project layout at repository root (`spotify_links.py`, `config.py`, `main.py`, `tests/`) per plan.md — no `src/` hierarchy.

---

## Phase 1: Setup

**Purpose**: Confirm a clean starting point so this feature's changes are attributable

- [X] T001 Baseline check at repo root: run `.venv/bin/python -m pytest` and `.venv/bin/python -m flake8 .` — both must pass before any change (quickstart.md prerequisite)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

No foundational tasks — US1 (the new link builder) has no dependency on US2 (the config cleanup), and vice versa; each stands on the existing codebase. Proceed directly to Phase 3.

---

## Phase 3: User Story 1 - Song Links Work Again, Without Any Spotify Credentials (Priority: P1) 🎯 MVP

**Goal**: Every chart song in the P.S. block links to Spotify search results built purely from title + artist — no API call, no credential, and a link can never fail to build.

**Independent Test**: Run a `--test` send for a birthday person born after 1958 and click each song link: each opens Spotify search results with the song visible (quickstart.md scenarios 2 and 4).

### Tests for User Story 1

- [X] T002 [P] [US1] Create tests/test_spotify_links.py: `search_url("Hey Jude", "The Beatles")` produces `https://open.spotify.com/search/Hey%20Jude%20The%20Beatles`; cases for `&` (e.g. artist `"X & Y"`), `/` (e.g. title `"AM/FM"`), apostrophes, umlauts/non-ASCII, and a long title+artist combination — each asserted to be a single valid path segment with no raw space/`&`/`/`/`#`/`?` (contracts/email-links.md; research R2)

### Implementation for User Story 1

- [X] T003 [US1] Rewrite spotify_links.py: delete `get_token`, `find_track_url`, `SpotifyError`, the `requests` import, `TOKEN_URL`/`SEARCH_URL`/`REQUEST_TIMEOUT`; add `search_url(title: str, artist: str) -> str` returning `"https://open.spotify.com/search/" + urllib.parse.quote(f"{title} {artist}", safe="")` (research R1, R2)
- [X] T004 [US1] Update `gather_chart_entries` in main.py: drop the `config` parameter, remove the token-fetch/per-song-link try/except block, and instead assign `entry.spotify_url = spotify_links.search_url(entry.title, entry.artist)` for every fetched entry; remove the per-song and token-failure log lines (research R5, R6)
- [X] T005 [US1] Update the call site in `send_to_person` in main.py: `gather_chart_entries(person, config)` → `gather_chart_entries(person)`

**Checkpoint**: `./run.sh --test` produces emails whose P.S. songs are all linked again, with zero Spotify credentials and zero network calls for links. US1 alone restores the feature the policy change broke.

---

## Phase 4: User Story 2 - Setup Works Without a Spotify Developer Account (Priority: P2)

**Goal**: `.secret.json` no longer needs `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`; a file that never mentions Spotify — or still has stale entries — works identically.

**Independent Test**: Remove both Spotify keys from `.secret.json` and run `--test`: the run completes normally and the email still shows linked songs (quickstart.md scenario 3).

### Tests for User Story 2

- [X] T006 [P] [US2] Update tests/test_config.py: remove `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` from `VALID_DATA`; add a case asserting `load_config` succeeds when a secrets file carries stale `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` entries (ignored, no error) (contracts/config-delta.md; FR-003)

### Implementation for User Story 2

- [X] T007 [US2] Edit config.py: remove `"SPOTIFY_CLIENT_ID"` and `"SPOTIFY_CLIENT_SECRET"` from `REQUIRED_KEYS`; remove `spotify_client_id`/`spotify_client_secret` fields from `AppConfig` and their assignment in `load_config` (research R3)
- [X] T008 [P] [US2] Update README.md: remove `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` from the required-keys list and any Spotify-developer-app setup instructions; add a line noting song links open Spotify search results (contracts/config-delta.md; FR-007)

**Checkpoint**: A `.secret.json` with only the six core keys (mail + sender) plus `OWNER_RECIPIENT` passes validation and produces a fully working, fully linked test email.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Full-suite verification and the constitution's test-before-real gate

- [X] T009 Full offline verification at repo root: `.venv/bin/python -m pytest` and `.venv/bin/python -m flake8 .` both clean (constitution Development Workflow)
- [X] T010 Link-quality spot check (SC-002, no mail involved): generate `search_url` for ≥10 historical chart songs and open each — at least 9 of 10 result pages must visibly show the intended song (quickstart.md scenario 2)
- [X] T011 Execute quickstart.md scenarios 3 and 4 end to end: run `--test` with Spotify keys removed from `.secret.json`, inspect the received email's P.S. block and click-through links; confirm feature 002's routing block and subject are unaffected (Principle III gate)
- [X] T012 Regression check: `git diff --stat` confirms `charts.py`, `content.py`, and `requirements.txt` are untouched, per the plan's Structure Decision that P.S. appearance can't regress because nothing that reads `spotify_url` changed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: empty — nothing blocks the stories
- **User Stories (Phases 3–4)**: fully independent — US1 touches spotify_links.py and main.py; US2 touches config.py and README.md; no shared files
- **Polish (Phase 5)**: after both stories

### User Story Dependencies

- **US1 (P1)**: independent — no dependency on US2
- **US2 (P2)**: independent — no dependency on US1 (though it's natural to land after US1 since both together are what makes a from-scratch setup credential-free)

### Within Each User Story

- US1: T002 (test) before T003 (implementation) — TDD; T003 before T004 (main.py calls the new function); T004 before T005 (same file, sequential)
- US2: T006 (test) before T007 (implementation) — TDD; T008 independent of T006/T007 (different file)

### Parallel Opportunities

- T002 (tests/test_spotify_links.py) ∥ T006 (tests/test_config.py) — different files, both can be written immediately after T001
- T003 (spotify_links.py) ∥ T007 (config.py) — different files, no shared state; US1 and US2 can proceed as two independent tracks
- T008 (README.md) ∥ any implementation task

## Parallel Example: US1 + US2 kickoff

```bash
# Different files, no dependencies — can start together after T001:
Task: "Write encoding test cases in tests/test_spotify_links.py"     # T002
Task: "Write Spotify-keys-optional test in tests/test_config.py"     # T006
Task: "Update README required-keys list"                             # T008
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 baseline, skip empty Phase 2
2. Complete Phase 3 (T002–T005)
3. **STOP and VALIDATE**: quickstart scenario 2 (link quality) + a `--test` send — song links work again; this alone fixes the reported problem, even before touching `.secret.json`'s required keys
4. US2 then removes the now-unnecessary credential requirement

### Incremental Delivery

1. US1 → links restored, credential-free (deployable: owner's existing `.secret.json` still has the old Spotify keys, they're just no longer used for anything — already fixes the breakage)
2. US2 → required-keys shrink, docs updated (deployable: new-owner setup is simpler; existing owners can optionally clean up their secrets file)
3. Polish → full gates, link-quality sample, quickstart run, regression check

---

## Notes

- Total: 12 tasks (T001–T012); net code deletion — no new dependencies, no new modules
- US1 and US2 touch disjoint files, so they can be implemented and committed as two separate, independently revertible changes despite both belonging to one feature
- Commit after each task or logical group; every commit should keep pytest + flake8 green
- After implementation, consider a follow-up PATCH amendment to `.specify/memory/constitution.md` (via `/speckit-constitution`) updating the Technology & Data Constraints clause that still names the Spotify Web API — flagged in plan.md, out of this task list's scope
