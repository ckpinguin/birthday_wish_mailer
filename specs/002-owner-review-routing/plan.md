# Implementation Plan: Owner Review Routing

**Branch**: `002-owner-review-routing` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-owner-review-routing/spec.md`

## Summary

Reroute every generated birthday greeting to the owner instead of the
birthday person: real runs deliver all mail to a new `OWNER_RECIPIENT`
address from `.secret.json`, with the intended recipient's name and address
shown in the subject and in a visually separated routing block prepended to
the otherwise unchanged inline greeting. The owner reviews, adds a personal
touch, deletes the routing block, and forwards manually. A real run without
`OWNER_RECIPIENT` fails fast (exit 1, zero sends); test mode keeps its
delivery target but carries the identical review format so the new layout is
verifiable via `--test` first. Logs record both the intended birthday person
and the actual delivery address for every send.

## Technical Context

**Language/Version**: Python ≥ 3.12 (unchanged from feature 001)

**Primary Dependencies**: unchanged — runtime `requests`, `beautifulsoup4`
(neither touched by this feature; all changes are stdlib); dev-only
`pytest`, `flake8`

**Storage**: local files — `.secret.json` gains one key (`OWNER_RECIPIENT`);
CSV files, templates, images unchanged

**Testing**: pytest (offline: routing-block/subject rendering, config
parsing, delivery-address selection) + flake8; end-to-end via
`./run.sh --test` per [quickstart.md](quickstart.md)

**Target Platform**: Linux homeserver (systemd timer, journald logs);
macOS for development

**Project Type**: single CLI application, flat module layout (unchanged)

**Performance Goals**: N/A — a handful of emails per day

**Constraints**: greeting portion of the mail must stay byte-identical to
pre-feature output (FR-006); no mode may deliver to a birthday person's
address (FR-001); new key stays untracked (Principle II); tests stay
offline

**Scale/Scope**: 4 existing modules touched (`config.py`, `content.py`,
`mailer.py`, `main.py`), ~2 new small functions, no new files except tests;
~60 LOC delta expected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Pre-research | Post-design |
| --- | ----------- | -------------- | ------------- |
| I | Simplicity First | PASS — no new dependencies, no new abstractions; one config key, one HTML block, one subject helper | PASS — redirection stays a one-line address choice in `main.run` (R1); no classes added, plain functions only (data-model.md) |
| II | Secrets & personal data out of repo | PASS — `OWNER_RECIPIENT` lives in `.secret.json`, untracked | PASS — contracts/README use placeholder addresses only (cli-and-config.md); tests use fixture data |
| III | Test mode before real sends | PASS — `--test` retained; FR-008 makes it carry the new format | PASS — review format is unconditional so `--test` verifies exactly what real runs send (R5); quickstart 3–4 gate real deployment; feature *strengthens* III (human reviews every real mail) |
| IV | Graceful degradation of enrichment | PASS — enrichment pipeline untouched | PASS — routing block is core content, not enrichment; degradation table of 001 still governs the greeting part (contracts/review-email.md) |
| V | Observable unattended runs | PASS — FR-009 requires intended + actual recipient in logs | PASS — log contract fixes format for success and failure lines (R7, contracts/review-email.md) |

No violations → Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-owner-review-routing/
├── plan.md                  # This file
├── research.md              # Phase 0: decisions R1–R7
├── data-model.md            # Phase 1: AppConfig delta, Recipient role change, ReviewEmail shape
├── quickstart.md            # Phase 1: validation scenarios 1–6
├── contracts/
│   ├── review-email.md      # headers, body structure, routing block, log lines
│   └── cli-and-config.md    # delta vs. frozen 001 contracts: semantics, .secret.json key, exit codes
└── tasks.md                 # Phase 2 (/speckit-tasks — not created by /speckit-plan)
```

### Source Code (repository root)

```text
config.py                # MODIFIED: load optional OWNER_RECIPIENT → AppConfig.owner_recipient (R2)
content.py               # MODIFIED: new render_routing_block() + review_subject() helpers;
                         #           compose_html() gains an optional leading-block parameter (R3, R4)
mailer.py                # MODIFIED: build_message()/send_greeting() take the subject as a parameter
                         #           (SUBJECT constant retired); transport logic unchanged
main.py                  # MODIFIED: real-mode startup guard for owner_recipient (exit 1, R2);
                         #           delivery address = owner in real mode (R1);
                         #           builds subject + routing block per person;
                         #           send/failure logs name intended + actual recipient (R7)

tests/
├── test_content.py      # EXTENDED: routing-block rendering/escaping, subject format,
│                        #           composed body starts with routing block, greeting part unchanged
├── test_config.py       # NEW: OWNER_RECIPIENT parsed when present, None when absent
└── test_recipients.py   # unchanged

README.md                # MODIFIED: document OWNER_RECIPIENT key + the review-and-forward workflow
```

**Structure Decision**: No new modules — the feature distributes naturally
over the existing one-responsibility-per-file layout (Principle I): config
parses the key, content renders owner-facing text, mailer stays a dumb
transport that now receives its subject, and `main.run` keeps owning routing
policy exactly where the test-mode redirect already lives (research R1). The
greeting-generation path is untouched, which is what makes the FR-006
byte-identity invariant cheap to guarantee and test.

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
