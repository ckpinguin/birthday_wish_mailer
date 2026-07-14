# Feature Specification: Modernize Codebase

**Feature Branch**: `001-modernize-codebase`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "Refactor the app, use Python >3.12 and throw away unnecessary libraries (for example if you can work with csv without pandas, go ahead). Also refactor all you want in order to use best practices and make the code clear, concise and understandeable."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unchanged Birthday Greetings (Priority: P1)

As the maintainer, after the modernization I run the mailer exactly as before and
every recipient receives the same birthday email they would have received from the
old code: same subject, same randomly chosen German greeting text with correct
salutation for the recipient's gender, same birthday image, and — for recipients
born 1958 or later — the same "top 3 charts on your birthday" postscript with
working song links.

**Why this priority**: The mails are the product. A refactor that changes or breaks
what recipients see is a regression, no matter how clean the code becomes. This is
the non-negotiable baseline (Constitution Principle III).

**Independent Test**: Run the app in test mode before and after the refactor for
the same test data (one recipient born ≥ 1958, one born earlier) and compare the
received emails side by side.

**Acceptance Scenarios**:

1. **Given** a recipient in the test list born after 1958, **When** the app runs in
   test mode, **Then** the received email contains a greeting from one of the three
   letter templates with correct name and salutation, the birthday image, and a
   postscript listing three chart songs with clickable links.
2. **Given** a recipient born before 1958, **When** the app runs in test mode,
   **Then** the received email contains the greeting and image but no chart
   postscript.
3. **Given** no person has a birthday today, **When** the app runs, **Then** no
   email is sent and the run reports this and ends successfully.

---

### User Story 2 - Extras Can Fail, the Greeting Cannot (Priority: P2)

As the maintainer, when the chart-lookup website changes its layout or the music
service rejects a lookup, the birthday person still gets their greeting email —
just without the chart postscript — and the log tells me what went wrong. Likewise,
if sending to one recipient fails, other recipients with the same birthday still
get their mail.

**Why this priority**: Today an enrichment failure crashes the whole run and the
birthday is silently missed — a direct violation of Constitution Principle IV. This
is the most valuable behavioral fix the refactor can deliver.

**Independent Test**: Point the app at an unreachable chart source (or simulate a
lookup failure) in test mode and verify the greeting still arrives and the failure
is logged.

**Acceptance Scenarios**:

1. **Given** the chart website is unreachable or returns unusable content, **When**
   the app processes a recipient born after 1958, **Then** the greeting email is
   still sent without the chart postscript and the failure appears in the run log.
2. **Given** the music-link lookup fails after charts were fetched, **When** the
   email is composed, **Then** the greeting is sent (with chart names but without
   links, or without the postscript) and the failure appears in the run log.
3. **Given** two recipients share a birthday and sending to the first one fails,
   **When** the run continues, **Then** the second recipient still receives their
   email and the run finishes with a failure status visible to the scheduler.

---

### User Story 3 - Lean Setup on a Current Python (Priority: P3)

As the maintainer, I can set the project up from scratch on my homeserver with a
current Python version (3.12 or newer, including the latest stable release) and
only a handful of third-party libraries, each of which is actually used.

**Why this priority**: Fewer dependencies mean fewer version pins that rot and
block Python upgrades (today's pins already block Python 3.13+). Valuable, but only
after correctness (P1) and resilience (P2) are secured.

**Independent Test**: Create a fresh environment on Python 3.12 and on the newest
stable Python, install the dependencies, and complete a test-mode run.

**Acceptance Scenarios**:

1. **Given** a fresh environment on the newest stable Python, **When** dependencies
   are installed and the app runs in test mode, **Then** installation and the run
   complete without errors.
2. **Given** the dependency list, **When** reviewed, **Then** it contains no unused
   entries and every remaining entry has a stated purpose the standard library
   cannot reasonably cover.

---

### User Story 4 - Safe Future Changes (Priority: P3)

As the maintainer, I can verify a future change is safe by running an automated
offline check (tests plus style check) that exercises the recipient-selection and
email-composition logic without sending any email or touching the network.

**Why this priority**: The git history shows rendering breakage is the recurring
defect class; an offline safety net catches those before the test-send step.

**Independent Test**: Run the check suite on a machine with networking disabled and
confirm it passes, sends nothing, and finishes quickly.

**Acceptance Scenarios**:

1. **Given** the repository on a machine without network access, **When** the check
   suite runs, **Then** all checks pass without sending email or contacting any
   external service.
2. **Given** a deliberate mistake in the email-composition logic (e.g., broken
   placeholder replacement), **When** the check suite runs, **Then** at least one
   check fails and names the problem.

---

### Edge Cases

- Recipient born on Feb 29: current behavior (greeting sent only in leap years, on
  the exact date match) is preserved; changing it is out of scope.
- Recipient born before 1958: no chart data exists — greeting without postscript
  (existing behavior, preserved).
- CSV rows that are inactive, lack an email address, or lack a complete birth date:
  skipped, as today.
- Configuration file missing or unreadable: the run stops with a clear error
  message and a failure status the scheduler can detect (today it exits with a
  success status — this changes).
- Greeting template or image file missing at compose time: the run reports a clear
  error; recipients already processed are unaffected.
- Chart source unreachable, layout changed, or returning fewer than three entries:
  greeting still sent; postscript omitted or shortened; failure logged.
- Two or more recipients share today's date: each is processed independently; one
  failure does not stop the others.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST produce recipient-visible emails equivalent to the
  current ones: same subject, same three German greeting templates with name,
  gender-appropriate salutation and sender placeholders filled, same inline
  birthday image, and the same chart postscript for recipients born 1958 or later.
  Invalid markup in the current output MAY be corrected as long as the rendered
  appearance in common mail clients is preserved or improved.
- **FR-002**: The system MUST read recipients from the existing CSV files with the
  existing columns (`firstname`, `gender`, `email`, `year`, `month`, `day`,
  `active`) and apply the existing selection rules: only active entries with an
  email address and a complete birth date whose month and day match today.
- **FR-003**: Chart lookup and song-link enrichment MUST be treated as optional:
  any failure in fetching, parsing, or link lookup MUST result in the greeting
  being sent without (or with reduced) enrichment, never in a lost greeting or an
  aborted run.
- **FR-004**: A failure while composing or sending one recipient's email MUST NOT
  prevent remaining recipients from being processed; the run MUST finish with a
  failure status if any recipient could not be served.
- **FR-005**: The system MUST run on Python 3.12 and newer, including the newest
  stable release, from a fresh environment.
- **FR-006**: Every third-party dependency MUST be removed unless it provides
  clearly more value than a standard-library solution; the remaining dependency
  list MUST be pinned and each entry's purpose documented.
- **FR-007**: Test mode MUST keep its current interface (`--test` flag, separate
  test CSV, all mail redirected to a test recipient) and MUST use the dedicated
  test-recipient setting from the configuration file, falling back to the current
  behavior (BCC address) when it is absent.
- **FR-008**: Fatal startup problems (missing/invalid configuration, missing data
  file) MUST terminate the run with a non-success status and a message naming the
  missing piece, so the scheduler surfaces the failure.
- **FR-009**: Each run MUST log: which recipients matched today, each enrichment
  lookup and its outcome, each email sent with its recipient, and every error with
  enough context to diagnose it from the log alone (Constitution Principle V).
- **FR-010**: All credentials and personal data MUST continue to live only in the
  existing untracked files; the refactor MUST NOT introduce any hardcoded
  credential, address, or real personal data (Constitution Principle II).
- **FR-011**: The recipient-selection and email-composition logic MUST be covered
  by automated checks that run offline, send no email, and complete quickly.
- **FR-012**: The codebase MUST pass the project's style check without suppression
  comments.

### Key Entities

- **Recipient**: A person from the birthday list — name, gender, email address,
  birth date, active flag.
- **Greeting**: The composed email — chosen template with placeholders filled,
  inline image, optional chart postscript.
- **Chart entry**: A song title, artist, and optional listening link for the
  recipient's birth date.
- **Run configuration**: Mail account, sender/BCC/test-recipient addresses, and
  music-service credentials from the untracked configuration file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a test recipient born after 1958 and one born before, test-mode
  emails produced after the refactor are visually equivalent to the ones produced
  before (greeting text, salutation, image, postscript with three working links /
  no postscript respectively), confirmed by side-by-side inspection.
- **SC-002**: The number of directly required third-party libraries drops from 17
  pinned entries to at most 4, with a one-line justification for each survivor.
- **SC-003**: A fresh setup plus successful test-mode run works on Python 3.12 and
  on the newest stable Python release, verified on both.
- **SC-004**: With the chart source unreachable, 100% of due greetings are still
  delivered in test runs, and the cause of the missing postscript is identifiable
  from the run log alone.
- **SC-005**: The offline check suite completes in under one minute, sends zero
  emails, performs zero network calls, and fails when a deliberate composition
  bug is introduced.
- **SC-006**: After a scheduled run, the questions "who matched today?" and "which
  mails were sent to whom?" are answerable from the run log alone.

## Assumptions

- "Python >3.12" is read as "Python 3.12 or newer, including the newest stable
  release" — the intent is that outdated dependency pins no longer dictate the
  Python version.
- Recipient-visible behavior is otherwise frozen: greeting texts, template
  selection by chance, subject line, image attachment, and the Feb-29/leap-year
  matching rule all stay as they are. Content or wording changes are out of scope.
- The proxy-related settings are absent from the active configuration file
  (verified), so the unused proxy support and its helper library can be removed;
  mail is sent directly.
- The configuration file already contains a dedicated test-recipient entry
  (verified) that the current code ignores; the refactor may honor it (FR-007)
  without any configuration change being required.
- The chart data continues to come from the same public chart archive via the
  existing scraping approach; switching data sources is out of scope.
- The existing entry point (`main.py` with optional `--test`) and the deployment
  wrapper (`run.sh`, systemd units) keep working without changes to the units.
- The CSV files keep their current format; no migration of recipient data is
  needed.
- Libraries currently pinned but not imported anywhere (e.g., a caching client) or
  only needed by the table library being replaced are confirmed removable.
