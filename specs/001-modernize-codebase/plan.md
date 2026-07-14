# Implementation Plan: Modernize Codebase

**Branch**: `001-modernize-codebase` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-modernize-codebase/spec.md`

## Summary

Refactor the birthday mailer to run on Python ≥ 3.12 with only two runtime
dependencies (requests, beautifulsoup4), replacing pandas with stdlib `csv`,
spotipy with direct Spotify Web API calls, and legacy MIME assembly with
`email.message.EmailMessage`. Recipient-visible emails stay equivalent; the
refactor additionally delivers constitution compliance that the current code
lacks: enrichment failures degrade gracefully instead of crashing the run,
per-recipient failures don't stop other sends, fatal errors exit non-zero, and
core logic gains an offline test suite plus clean flake8. Entry point
(`python main.py [--test]`), data-file formats, run.sh, and systemd units are
unchanged.

## Technical Context

**Language/Version**: Python ≥ 3.12 (dev venv: 3.12.13; verify also on newest stable, currently 3.14)

**Primary Dependencies**: runtime: `requests`, `beautifulsoup4` (only these two — see research R1–R4); dev-only: `pytest`, `flake8`

**Storage**: local files — CSV recipient lists, JSON config (`.secret.json`), text templates, PNG images; no database, no persistent state

**Testing**: pytest (offline; HTML/CSV fixtures, no network, no SMTP) + flake8; end-to-end via `./run.sh --test` per quickstart

**Target Platform**: Linux homeserver (systemd timer, journald logs); macOS for development

**Project Type**: single CLI application, flat module layout

**Performance Goals**: N/A — a handful of emails per day; offline check suite must finish < 1 min (SC-005)

**Constraints**: recipient-visible email equivalence (FR-001); CLI/file contracts frozen (contracts/); secrets and personal data remain untracked (Principle II); tests must run without network

**Scale/Scope**: dozens of CSV rows, ~350 LOC application code, 6 modules + tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Pre-research | Post-design |
| --- | ----------- | -------------- | ------------- |
| I | Simplicity First | PASS — dependency count 17→2, flat modules, stdlib where reasonable, no new abstractions (research R1, R10) | PASS — design adds no package hierarchy, no template engine, no config framework (R5, R10) |
| II | Secrets & personal data out of repo | PASS — config/data file locations and gitignore untouched | PASS — contracts specify untracked files; logs exclude credentials (contracts/cli.md) |
| III | Test mode before real sends | PASS — `--test` interface preserved (FR-007) | PASS — quickstart step 3 mandates test-send comparison before real runs |
| IV | Graceful degradation of enrichment | PASS — core requirement FR-003; fixes current violation (crash on chart failure) | PASS — degradation table in contracts/email-output.md; per-recipient isolation (R6) |
| V | Observable unattended runs | PASS — FR-009 log requirements | PASS — log format contract in contracts/cli.md; meaningful exit codes for systemd (R6) |

No violations → Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-modernize-codebase/
├── plan.md              # This file
├── research.md          # Phase 0: dependency & design decisions R1–R10
├── data-model.md        # Phase 1: Recipient, AppConfig, ChartEntry, Greeting
├── quickstart.md        # Phase 1: validation scenarios 1–6
├── contracts/
│   ├── cli.md           # invocation, files, exit codes, log format (frozen)
│   ├── email-output.md  # recipient-visible mail structure + degradation rules
│   └── data-files.md    # CSV / .secret.json / template / image formats (frozen)
└── tasks.md             # Phase 2 (/speckit-tasks — not created by /speckit-plan)
```

### Source Code (repository root)

```text
main.py                  # entry point (kept): CLI args, logging setup, orchestration, exit codes
config.py                # NEW: load/validate .secret.json → AppConfig dataclass
recipients.py            # NEW: Recipient dataclass, CSV loading, selection rules (replaces pandas usage in main.py)
charts.py                # RENAMED from billboard_timemachine.py: fetch+parse top 3, proper exceptions
spotify_links.py         # REPLACES spotifier.py: client-credentials token + track search via requests
content.py               # NEW: template choice, placeholder filling, HTML + postscript composition
mailer.py                # REWRITTEN: EmailMessage + STARTTLS send; proxy support removed

tests/
├── test_recipients.py   # selection rules against fixture CSV (incl. skip/edge rows)
├── test_content.py      # placeholder filling, salutation, postscript, valid-HTML checks
├── test_charts.py       # parser against saved Billboard HTML fixture
└── fixtures/            # birthdays_fixture.csv, billboard_sample.html

requirements.txt         # runtime: requests, beautifulsoup4 (pinned)
requirements-dev.txt     # NEW: pytest, flake8 (pinned)
```

**Structure Decision**: Flat top-level modules, one per responsibility (research
R10). No src/ package: nothing imports this project and ~350 LOC don't justify
the indirection (Principle I). Import-time side effects (config reads at class
body, module-level `.secret.json` loads) are eliminated so tests can import
every module offline. Deleted: `spotifier.py`, `billboard_timemachine.py`
(renamed/replaced), pandas/spotipy/PySocks/redis and friends from
requirements.txt. `Procfile` and `fly.toml` (dead cloud-deploy relics) are
removed as part of the cleanup.

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
