# Tasks: Modernize Codebase

**Input**: Design documents from `/specs/001-modernize-codebase/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included — the spec explicitly requires an offline test suite (FR-011, US4).

**Organization**: Grouped by user story; stories are ordered US1 → US2 → US3 → US4
because they layer onto the same small codebase (see Dependencies).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: New dependency baseline and lint configuration

- [ ] T001 Create and switch to feature branch `001-modernize-codebase` (constitution: multi-file changes go through a feature branch)
- [ ] T002 [P] Rewrite requirements.txt to exactly two pinned runtime deps: `requests`, `beautifulsoup4` (research R1–R4)
- [ ] T003 [P] Create requirements-dev.txt with pinned `pytest` and `flake8` (research R8)
- [ ] T004 [P] Create .flake8 config excluding `.venv`, `__pycache__` so `flake8 .` lints only project code
- [ ] T005 Refresh venv from the new requirements files (`.venv/bin/pip install -r requirements.txt -r requirements-dev.txt` after uninstalling old pins or recreating `.venv`) and verify `import requests, bs4` works

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Side-effect-free configuration loading that every story builds on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create config.py: `AppConfig` dataclass (fields per data-model.md → AppConfig) and `load_config(path=".secret.json")` with required-key validation raising a `ConfigError`; no import-time side effects (research R10); do not read `PROXY_HOST`/`PROXY_PORT` (R4)

**Checkpoint**: `python -c "from config import load_config"` works offline with no file reads at import

---

## Phase 3: User Story 1 - Unchanged Birthday Greetings (Priority: P1) 🎯 MVP

**Goal**: Full refactored pipeline producing recipient-visible emails equivalent to legacy output (contracts/email-output.md)

**Independent Test**: `./run.sh --test` with a today-dated test row born ≥ 1958 and one born < 1958; compare received mails side by side with legacy output (quickstart §3)

### Implementation for User Story 1

- [ ] T007 [P] [US1] Create recipients.py: `Recipient` dataclass + `load_recipients(csv_path)` + `due_today(recipients, today)` implementing the selection rules in data-model.md → Recipient (skip invalid rows with a warning instead of crashing)
- [ ] T008 [P] [US1] Create charts.py (replaces billboard_timemachine.py): `fetch_top_three(date) -> list[tuple[str, str]]` using requests + BeautifulSoup with the existing CSS selectors; raise a proper `ChartsError` on HTTP/parse failure (fixes the legacy `raise "string"` bug, research R6)
- [ ] T009 [P] [US1] Create spotify_links.py (replaces spotifier.py): client-credentials token request + `find_track_url(title, artist) -> str | None` via the Spotify Web API search endpoint (research R2 — no OAuth flow, no spotipy)
- [ ] T010 [P] [US1] Create content.py: random template/image choice (count constants in one place per contracts/data-files.md), `[TITLE]`/`[NAME]`/`[SENDER]` replacement, chart-postscript rendering, and valid-HTML document assembly fixing the malformed `</p` tag (research R5, contracts/email-output.md)
- [ ] T011 [US1] Rewrite mailer.py: `send_greeting(config, to_addr, html, image_path)` using `email.message.EmailMessage` with HTML alternative + CID inline image, STARTTLS to `MAILHOST:PORT`; config passed in (no import-time `.secret.json` read); proxy code removed (research R4, R5)
- [ ] T012 [US1] Rewrite main.py: argparse (`-t/--test`), logging setup (stdout, `%(levelname)s %(message)s`, research R7), orchestration recipients → charts → links → content → mailer; test mode uses `TEST_RECIPIENT` with fallback to `BCC_ADDR` (FR-007); entry point `python main.py [--test]` unchanged (contracts/cli.md)
- [ ] T013 [US1] Verify US1 end-to-end: adjust TEST_birthdays.csv dates to today, run `./run.sh --test`, check both received mails against contracts/email-output.md (constitution Principle III)

**Checkpoint**: Refactored app sends equivalent mails in test mode — MVP done

---

## Phase 4: User Story 2 - Extras Can Fail, the Greeting Cannot (Priority: P2)

**Goal**: Enrichment failures degrade to a plain greeting; one recipient's failure never blocks others; exit codes surface failures to systemd (contracts/cli.md)

**Independent Test**: Point charts at an unreachable host in a scratch copy → greeting still arrives, WARNING logged, exit 0; remove .secret.json → exit 1 (quickstart §4–5)

### Implementation for User Story 2

- [ ] T014 [US2] In main.py wrap per-recipient enrichment (charts + links) in try/except: on any failure log WARNING with context and continue with empty/partial entries (FR-003, degradation table in contracts/email-output.md)
- [ ] T015 [US2] In main.py isolate per-recipient compose/send: one failure logs ERROR, loop continues, run exits 2 if any due recipient was not served (FR-004, contracts/cli.md exit codes)
- [ ] T016 [US2] In main.py handle fatal startup errors (ConfigError, missing CSV): log a message naming the missing piece, exit 1 — replaces legacy `exit(0)` (FR-008)
- [ ] T017 [US2] Align all log lines with the format in contracts/cli.md (matched recipients, per-lookup outcome, per-send outcome; no credentials) (FR-009)
- [ ] T018 [US2] Verify US2: simulate chart failure and missing config per quickstart §4–§5; confirm mail delivery, WARNING, and exit codes 0/1

**Checkpoint**: A broken Billboard page can no longer cost anyone their birthday mail

---

## Phase 5: User Story 3 - Lean Setup on a Current Python (Priority: P3)

**Goal**: Only justified dependencies remain; dead code and cloud relics gone; fresh install works on 3.12 and newest stable Python

**Independent Test**: Fresh venv on Python 3.12 and 3.14 → install + `./run.sh --test` succeed (quickstart §1)

### Implementation for User Story 3

- [ ] T019 [P] [US3] Delete replaced/dead files: spotifier.py, billboard_timemachine.py, Procfile, fly.toml (plan Structure Decision)
- [ ] T020 [P] [US3] Add one-line justification for each runtime dependency in README.md (SC-002, FR-006)
- [ ] T021 [P] [US3] Update README.md Requirements section: Python ≥ 3.12 (drop the "3.10–3.12 pin ceiling" note)
- [ ] T022 [US3] Verify fresh installs: `rm -rf .venv && PYTHON=python3.12 ./run.sh --help`, then scratch-copy check with `PYTHON=python3` (3.14) — both must bootstrap and print usage (SC-003); finish with one `./run.sh --test`

**Checkpoint**: `pip list` shows requests + beautifulsoup4 (+ transitives) only; installs clean on 3.12 and 3.14

---

## Phase 6: User Story 4 - Safe Future Changes (Priority: P3)

**Goal**: Offline pytest suite + clean flake8 catching composition/selection regressions without network or mail (FR-011, FR-012)

**Independent Test**: Suite passes with networking off, sends nothing, finishes < 1 min; a deliberately broken placeholder replacement makes it fail (quickstart §2)

### Implementation for User Story 4

- [ ] T023 [P] [US4] Create tests/fixtures/birthdays_fixture.csv with synthetic persons only (no real data — Principle II) covering: match today, inactive, missing email, incomplete date, unparsable year, born < 1958
- [ ] T024 [P] [US4] Create tests/fixtures/billboard_sample.html — trimmed saved Billboard chart page with ≥ 3 entries matching the selectors used in charts.py
- [ ] T025 [P] [US4] Create tests/test_recipients.py: selection rules against the fixture CSV incl. skip cases and date matching (FR-002)
- [ ] T026 [P] [US4] Create tests/test_content.py: placeholder filling, f/m salutation, postscript with and without links, no leftover `[NAME]`-style placeholders, output parses as valid HTML
- [ ] T027 [P] [US4] Create tests/test_charts.py: parser returns 3 (title, artist) tuples from the fixture; empty/garbage HTML raises ChartsError
- [ ] T028 [US4] Run `.venv/bin/python -m pytest` and `.venv/bin/python -m flake8 .`: all green, zero `# noqa` in the codebase, suite < 1 min offline (SC-005); negative check per quickstart §2

**Checkpoint**: All four stories independently verified

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T029 Run the full quickstart.md validation pass (§1–§6) and record results in specs/001-modernize-codebase/quickstart.md as checked-off notes
- [ ] T030 Amend the constitution's Technology & Data Constraints via /speckit-constitution: Python 3.12+, pandas/spotipy removed from the stack list (PATCH bump)
- [ ] T031 Commit on the feature branch and open a PR to main per constitution Development Workflow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → user stories
- **US1 (Phase 3)**: needs T006 (config); is the whole refactored pipeline — everything else layers on it
- **US2 (Phase 4)**: modifies main.py from US1 → strictly after US1
- **US3 (Phase 5)**: deleting spotifier.py/billboard_timemachine.py is only safe once US1 no longer imports them → after US1 (deletion also removes the last `# noqa`s, unblocking T028)
- **US4 (Phase 6)**: tests import the US1 modules → after US1; T028 (flake8 clean) additionally needs T019 (old files deleted) → run Phase 6 after Phase 5
- **Polish (Phase 7)**: after all stories

### Within-story ordering

- T007–T010 [P] are independent new files → parallel; T011 needs T006; T012 needs T007–T011; T013 last
- T014–T017 all touch main.py → sequential; T018 last
- T019–T021 [P] parallel; T022 last
- T023–T027 [P] parallel (new files); T028 last

### Parallel Opportunities

```text
Phase 1: T002 + T003 + T004 together
Phase 3: T007 + T008 + T009 + T010 together (four new modules, no shared files)
Phase 5: T019 + T020 + T021 together
Phase 6: T023 + T024 + T025 + T026 + T027 together (all new test files)
```

---

## Implementation Strategy

**MVP first**: Phases 1–3 (T001–T013) deliver the complete refactored mailer with
equivalent output — stop there and validate with a real test send before
continuing. Each later phase is an independent, deployable increment:
US2 makes it resilient, US3 makes it lean, US4 makes it safe to change.

Commit after each phase checkpoint; the final PR (T031) carries the whole
feature branch. Note that T013/T018/T022 involve real test-mode email sends —
inspect the test inbox before proceeding past each checkpoint (Principle III).
