# Tasks: Owner Review Routing

**Input**: Design documents from `/specs/002-owner-review-routing/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R7), data-model.md, contracts/, quickstart.md

**Tests**: Included — plan.md's Technical Context mandates offline pytest coverage for the new behaviors (routing block, subject, config parsing), and the constitution requires a flake8-clean, offline-testable result.

**Organization**: Tasks are grouped by user story so each story is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

Flat single-project layout at repository root (`config.py`, `content.py`, `mailer.py`, `main.py`, `tests/`) per plan.md — no `src/` hierarchy.

---

## Phase 1: Setup

**Purpose**: Confirm a clean starting point so feature regressions are attributable

- [ ] T001 Baseline check at repo root: run `.venv/bin/python -m pytest` and `.venv/bin/python -m flake8 .` — both must pass before any change (quickstart.md prerequisite)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

No foundational tasks — the feature-001 codebase is the foundation; every change belongs to a specific user story. Proceed directly to Phase 3.

---

## Phase 3: User Story 1 - Greetings Are Delivered to the Owner (Priority: P1) 🎯 MVP

**Goal**: Real runs deliver every generated greeting to `OWNER_RECIPIENT` instead of the birthday person; missing key aborts before any send; logs name intended + actual recipient.

**Independent Test**: With `OWNER_RECIPIENT` configured, a real-mode run delivers only to the owner (birthday person's inbox stays empty); without the key, the run exits 1 with zero sends (quickstart.md scenario 5).

### Implementation for User Story 1

- [ ] T002 [P] [US1] Extend `AppConfig` in config.py with `owner_recipient: str | None = None` and read the optional `OWNER_RECIPIENT` key in `load_config()` (research R2; do NOT add to `REQUIRED_KEYS`)
- [ ] T003 [US1] Create tests/test_config.py: `owner_recipient` populated when `OWNER_RECIPIENT` present, `None` when absent; existing required-key validation unaffected (fixture-style JSON via `tmp_path`, offline)
- [ ] T004 [US1] Add real-mode startup guard in `run()` in main.py: if not test mode and `config.owner_recipient` is falsy, log `cannot start: real mode needs OWNER_RECIPIENT in .secret.json` and return 1 before any send (FR-003; message style per contracts/cli-and-config.md, mirroring the existing test-mode guard)
- [ ] T005 [US1] Change delivery-address selection in `run()` in main.py: `to_addr = test_recipient if test_mode else config.owner_recipient` — `person.email` is no longer a delivery target in any mode (FR-001, research R1)
- [ ] T006 [US1] Implement the log contract in main.py and mailer.py: per-send success line `sent mail for {firstname} (intended: {email}) to {delivery_addr}` and failure line naming the birthday person (contracts/review-email.md, research R7); drop/adjust the old `sent mail to %s` line in mailer.py so logs aren't duplicated or misleading

**Checkpoint**: `./run.sh --test` behaves as before (delivery-wise); a real run delivers everything to the owner (still in the old mail format — that's US2/US3); missing-key guard verified. US1 is a shippable safety improvement on its own.

---

## Phase 4: User Story 2 - The Owner Can See Who the Greeting Is For (Priority: P2)

**Goal**: Every review email identifies the intended recipient — name + address in the subject line and as copyable plain text in a routing block inside the body.

**Independent Test**: Trigger a `--test` run for a known birthday row and verify the received mail's subject is `Geburtstagsmail für {firstname} ({email})` and the body's routing block shows name and address as selectable text (quickstart.md scenario 3).

### Implementation for User Story 2

- [ ] T007 [P] [US2] Add `review_subject(firstname, email)` helper in content.py returning `Geburtstagsmail für {firstname} ({email})` (research R4)
- [ ] T008 [US2] Add `render_routing_block(firstname, email)` in content.py: dashed-border grey `<div>` with inline CSS, HTML-escaped `Für: {firstname} <{email}>` line plus removal hint `Diesen Kasten vor dem Weiterleiten entfernen.` exactly per contracts/review-email.md (research R3)
- [ ] T009 [US2] Extend `compose_html()` in content.py with a leading-block parameter (default `""`) emitted as the first element inside `<body>`, before the greeting paragraph
- [ ] T010 [P] [US2] Change `build_message()`/`send_greeting()` in mailer.py to take the subject as a parameter; retire the fixed `SUBJECT` constant (transport logic otherwise untouched)
- [ ] T011 [US2] Wire it together in `send_to_person()` in main.py: build subject via `review_subject`, routing block via `render_routing_block`, pass both through `compose_html`/`send_greeting` — unconditionally, so test mode carries the identical review format (FR-008, research R5)
- [ ] T012 [US2] Extend tests/test_content.py: subject contains name and address; routing block HTML-escapes specials (e.g. name with `&`) and contains the address as plain text with no `mailto:` link; `compose_html` places the block first in `<body>`

**Checkpoint**: A `--test` run now delivers fully labeled review emails; multiple due rows are distinguishable from the inbox list alone.

---

## Phase 5: User Story 3 - The Greeting Is Forward-Ready (Priority: P3)

**Goal**: Prove the greeting is inline, renders byte-identically to pre-feature output beneath a visually separated routing block, and survives the review→personalize→forward workflow.

**Independent Test**: Forward a received review email after deleting the routing block and adding a sentence; the forwarded copy renders the greeting correctly with no routing traces (quickstart.md scenario 4).

### Implementation for User Story 3

- [ ] T013 [US3] Add FR-006 invariant tests in tests/test_content.py: `compose_html` with an empty leading block is byte-identical to the pre-feature composition; with a block, removing the block substring yields exactly the same document; block styling assertions (inline `border`/`background` CSS, removal-hint text) per contracts/review-email.md
- [ ] T014 [US3] Forward rehearsal (manual validation): execute quickstart.md scenario 4 — forward a `--test` review mail to the test address with the block deleted and a personal sentence added; confirm clean rendering (SC-003)

**Checkpoint**: All three stories independently verified; the full owner workflow works end to end.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, full-suite verification, and the constitution's test-before-real gate

- [ ] T015 [P] Document the `OWNER_RECIPIENT` key and the review-and-forward workflow in README.md (placeholder address only — Principle II)
- [ ] T016 Full offline verification at repo root: `.venv/bin/python -m pytest` and `.venv/bin/python -m flake8 .` both clean (constitution Development Workflow)
- [ ] T017 Execute quickstart.md scenarios 2, 3, and 5 end to end: add the key to `.secret.json`, inspect a real `--test` send against contracts/review-email.md, and run the safe negative test for the missing-key guard (Principle III gate; scenario 6 happens after deployment on the server)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: empty — nothing blocks the stories
- **User Stories (Phases 3–5)**: US1 and US2 are code-independent until their main.py tasks (T004–T006 vs T011) — sequence those; US3 depends on US2 (it tests the block US2 built)
- **Polish (Phase 6)**: after all stories

### User Story Dependencies

- **US1 (P1)**: independent — touches config.py, tests/test_config.py, main.py (`run()`), mailer.py log line
- **US2 (P2)**: independent of US1's logic but shares main.py; its content.py/mailer.py tasks (T007–T010) can start anytime, final wiring (T011) after US1's main.py edits to avoid conflicts
- **US3 (P3)**: requires US2 complete (verifies the routing block and composition invariants)

### Within Each User Story

- US1: T002 → T003 (test imports the new field); T004 → T005 → T006 (same function/file)
- US2: T007/T008/T009 sequential (all content.py); T010 parallel to those; T011 after T007–T010; T012 after T007–T009
- US3: T013 after US2; T014 after T013 (rehearse on verified output)

### Parallel Opportunities

- T002 (config.py) ∥ T007–T009 (content.py) ∥ T010 (mailer.py) — three files, no shared state
- T015 (README.md) ∥ any earlier task once behavior is settled

## Parallel Example: US1 + US2 kickoff

```bash
# Different files, no dependencies — can start together after T001:
Task: "Extend AppConfig with owner_recipient in config.py"           # T002
Task: "Add review_subject helper in content.py"                      # T007
Task: "Take subject as parameter in mailer.py build_message"         # T010
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 baseline, skip empty Phase 2
2. Complete Phase 3 (T002–T006)
3. **STOP and VALIDATE**: quickstart scenario 5 (guard) + a `--test` send — mail already only ever reaches owner/test addresses; the feature's safety core is live
4. US2/US3 then add the labeling and forward-readiness on top

### Incremental Delivery

1. US1 → redirection + guard + logs (deployable: owner gets old-format mail, recipients get nothing)
2. US2 → labeled subject + routing block (deployable: full daily workflow usable)
3. US3 → invariants proven + forward rehearsal (workflow friction verified away)
4. Polish → README + full gates + quickstart run

---

## Notes

- Total: 17 tasks (T001–T017); no new dependencies, no new modules — matches plan.md's ~60 LOC estimate
- main.py is touched by both US1 and US2: keep T004–T006 merged/committed before starting T011
- Commit after each task or logical group; every commit should keep pytest + flake8 green
- The real-mode send path can never be exercised against real recipients during development — that is the point of the feature; all end-to-end validation goes through `--test` (Principle III)
