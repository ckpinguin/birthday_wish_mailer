<!--
Sync Impact Report
==================
Version change: (template, unversioned) → 1.0.0 (initial ratification)
Modified principles: none (initial adoption — all five principles newly defined)
Added sections:
  - Core Principles (I–V)
  - Technology & Data Constraints
  - Development Workflow
  - Governance
Removed sections: none (all template placeholders filled)
Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no change needed (Constitution Check
    gate is derived dynamically from this file)
  - .specify/templates/spec-template.md — ✅ no change needed (no constitution-
    specific references)
  - .specify/templates/tasks-template.md — ✅ no change needed (no constitution-
    specific references)
  - .claude/skills/speckit-*/SKILL.md — ✅ no change needed (generic references
    to .specify/memory/constitution.md only)
Follow-up TODOs: none
-->

# Birthday Wish Mailer Constitution

## Core Principles

### I. Simplicity First

The project is a small, single-purpose personal tool. Code MUST stay readable and
directly adaptable: prefer plain functions and explicit, step-by-step logic over
frameworks, abstraction layers, or clever one-liners. A slightly verbose solution
that a future reader understands immediately beats a compact one that needs
decoding. New dependencies, services, or architectural layers MUST be justified by
a concrete current need (YAGNI), not by anticipated future requirements.

**Rationale**: The existing codebase deliberately favors clarity (explicit filter
functions, sequential composition). Keeping that bar low is what makes a
maintained-by-one-person tool sustainable.

### II. Secrets and Personal Data Stay Out of the Repo

All credentials (SMTP login, Spotify API keys, sender/BCC addresses) MUST be read
from `.secret.json` (or environment variables) and MUST never be committed.
Recipient data (`birthdays.csv`, `TEST_birthdays.csv`) contains real names, birth
dates, and email addresses of private individuals and MUST remain untracked, as
enforced by `.gitignore` today. No code change may hardcode a credential or a real
recipient address, and personal data MUST NOT appear in committed test fixtures,
documentation, or example output.

**Rationale**: The repository is public-facing; a single leaked credential or
recipient list is irreversible.

### III. Test Mode Before Real Sends (NON-NEGOTIABLE)

Any change that affects email content, template rendering, attachments, or SMTP
delivery MUST be verified by running the app with `--test` (test CSV plus test
recipient from `.secret.json`) and inspecting the received email before the change
runs against the real recipient list. Real recipients MUST never receive an email
produced by unverified rendering code.

**Rationale**: Emails cannot be unsent. The git history (repeated HTML-formatting
fix commits) shows rendering breakage is the most common defect class in this
project.

### IV. Graceful Degradation of Enrichment Content

The core deliverable is the birthday greeting email. Enrichment content (Billboard
chart lookup, Spotify links, images) is optional garnish: failure or
unavailability of any enrichment source (network error, scraping breakage, birth
year before 1958, missing Spotify match) MUST NOT prevent the core greeting from
being sent. Enrichment failures MUST be handled by omitting the extra content, not
by aborting the run.

**Rationale**: A plain "Happy Birthday" that arrives beats a rich email that
doesn't. External scrape targets and APIs break without notice.

### V. Observable Unattended Runs

The app runs unattended on a schedule (Fly.io). Every run MUST emit output
sufficient to reconstruct what happened from logs alone: which persons matched
today's date, which enrichment lookups ran (and their outcomes), and each mail
send with its recipient. Errors MUST be reported with enough context (URL, status
code, person being processed) to diagnose the failure without re-running locally.

**Rationale**: When a scheduled run fails silently, someone's birthday gets
missed; the logs are the only witness.

## Technology & Data Constraints

- **Language**: Python 3.10+ (the code uses modern union syntax such as
  `str | None`).
- **Core stack**: pandas for CSV handling, requests + BeautifulSoup for Billboard
  scraping, spotipy for Spotify lookups, stdlib `smtplib`/`email.mime` for
  delivery. Replacements require justification under Principle I.
- **Dependencies**: pinned with exact versions in `requirements.txt`.
- **Data files**: recipient data is CSV with the columns `firstname`, `gender`,
  `email`, `year`, `month`, `day`, `active`; the `active` flag and missing-field
  filtering MUST be respected by any new data consumer.
- **Email content**: German-language templates in `letter_templates/` using the
  placeholders `[NAME]`, `[TITLE]`, `[SENDER]`; images in `images/`. Generated
  HTML MUST be valid enough to render correctly in common mail clients.
- **Deployment**: Fly.io (app `birthday-wish-mailer`, region `ams`), configured
  via `fly.toml`.

## Development Workflow

- **Verification gate**: before deploying, run `python main.py --test` and confirm
  the test email renders correctly (Principle III).
- **Style**: keep code flake8-clean at the default line length; use `# noqa` only
  for deliberate, isolated exceptions (e.g., long literal HTML strings).
- **Branching**: small fixes may go directly to `main`; multi-file or behavioral
  changes SHOULD go through a feature branch and pull request, as established with
  prior feature work.
- **Spec-driven changes**: new features SHOULD flow through the Spec Kit pipeline
  (`/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`)
  with artifacts under `specs/`.

## Governance

This constitution supersedes ad-hoc habits for all changes to this repository.
Amendments are made by editing `.specify/memory/constitution.md` with a semantic
version bump (MAJOR: principle removal or redefinition; MINOR: new principle or
materially expanded guidance; PATCH: clarification or wording) and an updated Sync
Impact Report comment. The `/speckit-plan` Constitution Check gate MUST evaluate
each feature plan against Principles I–V, and violations MUST be either resolved
or explicitly justified in the plan's Complexity Tracking table. Reviews of pull
requests SHOULD verify compliance, with special weight on Principles II and III,
whose violation is irreversible.

**Version**: 1.0.0 | **Ratified**: 2026-07-14 | **Last Amended**: 2026-07-14
