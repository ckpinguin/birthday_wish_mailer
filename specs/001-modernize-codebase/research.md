# Phase 0 Research: Modernize Codebase

All Technical Context unknowns resolved. No NEEDS CLARIFICATION markers remained
in the spec; research below records the dependency and design decisions with
rationale.

## R1: CSV handling — drop pandas, use stdlib `csv`

- **Decision**: Replace `pandas.read_csv` + DataFrame filtering with
  `csv.DictReader` and a `Recipient` dataclass; selection rules become plain
  Python predicates.
- **Rationale**: The app reads one small CSV (dozens of rows) and applies four
  simple filters. pandas pulls in numpy, pytz, tzdata, python-dateutil, six — and
  its old pin is exactly what blocks Python 3.13+. stdlib `csv` removes six
  packages and the version ceiling at zero functional cost.
- **Alternatives considered**: Keep pandas (rejected: massively oversized for the
  job, blocks current Python); upgrade pandas pin (rejected: still oversized).

## R2: Spotify links — drop spotipy, call the Web API directly with `requests`

- **Decision**: Replace spotipy with two direct HTTPS calls: obtain an
  app-only token via the Client Credentials flow
  (`POST https://accounts.spotify.com/api/token`), then
  `GET https://api.spotify.com/v1/search?type=track&q=track:<title> artist:<name>`
  and take the first result's external URL. On any failure, return no link.
- **Rationale**:
  1. spotipy's install requirements pull in `redis` and `six` — that is why the
     unused `redis` pin sits in requirements.txt today.
  2. **Deployment hazard found during research**: the current `Spotifier` class
     constructs a `SpotifyOAuth` flow (user authorization, browser redirect) and
     calls `get_access_token()` before switching to client credentials. On a
     headless homeserver with no cached token this blocks or crashes the run.
     The search endpoint needs only client credentials; the OAuth dance is
     vestigial and gets removed.
  3. The whole need is ~30 lines with `requests`, which stays as a dependency
     anyway (R3).
- **Alternatives considered**: Keep spotipy (rejected: drags redis/six, keeps the
  OAuth hazard hidden); drop Spotify links entirely (rejected: changes the
  recipient-visible email, violating FR-001).

## R3: Billboard scraping — keep `requests` + `beautifulsoup4`

- **Decision**: Keep both as the only two runtime dependencies.
- **Rationale**: Scraping billboard.com's rendered HTML with stdlib
  `html.parser`/regex would be brittle and unreadable — exactly what Principle I
  forbids. bs4's CSS selectors are the clearest tool for the job; requests is the
  de-facto standard HTTP client and also serves R2. Justifications recorded per
  FR-006/SC-002.
- **Alternatives considered**: stdlib `urllib.request` + manual parsing
  (rejected: less readable, no functional gain); httpx (rejected: no need for
  async, requests is sufficient and better known).

## R4: Proxy support — remove entirely

- **Decision**: Delete the SOCKS proxy branch in the mailer and the PySocks
  dependency.
- **Rationale**: Verified that the active `.secret.json` contains no
  `PROXY_HOST`/`PROXY_PORT` keys; the homeserver sends directly. Dead
  configuration paths are complexity without value (Principle I).
- **Alternatives considered**: Keep it "just in case" (rejected: YAGNI; git
  history preserves it if ever needed again).

## R5: Email construction — modern stdlib `email.message.EmailMessage`

- **Decision**: Replace `MIMEMultipart`/`MIMEText`/`MIMEImage` assembly with
  `EmailMessage.add_alternative(html, subtype="html")` plus
  `add_related`/CID for the inline image. Fix the malformed `</p` tag and build
  valid HTML while keeping the rendered appearance identical (FR-001 allows
  markup correction).
- **Rationale**: `EmailMessage` is the documented modern API (Python ≥ 3.6),
  produces correct MIME structure, and removes the hand-rolled
  `<img src="cid:image1">` afterthought attachment. The repeated
  "had to fix html formatting" commits show the current string assembly is
  error-prone; composition will be unit-tested offline (FR-011).
- **Alternatives considered**: Keep MIME classes (rejected: legacy API, current
  output contains invalid markup); template engine like Jinja2 (rejected: new
  dependency for three placeholders — YAGNI).

## R6: Error handling & exit codes

- **Decision**:
  - Replace the broken `raise "string"` (a latent `TypeError`) with proper
    exceptions.
  - Wrap enrichment (charts + links) per recipient in a try/except that logs and
    degrades to a plain greeting (FR-003).
  - Wrap per-recipient compose/send so one failure doesn't stop the loop; track
    failures and exit non-zero at the end if any recipient was not served
    (FR-004).
  - Missing/invalid config or data file: log a clear message and exit with
    status 1 (today: exit 0 — changed per FR-008 so systemd flags the failure).
- **Rationale**: Constitution Principles IV and V; systemd `OnFailure`/status
  visibility requires meaningful exit codes.

## R7: Logging — stdlib `logging` to stdout

- **Decision**: Replace `print` with the `logging` module, INFO level to stdout,
  format `%(levelname)s %(message)s` (journald adds timestamps itself). Log:
  matched recipients, each enrichment attempt/outcome, each send, all errors with
  context (FR-009).
- **Rationale**: Levels make errors greppable in journalctl; stdout keeps the
  run.sh/systemd contract unchanged.
- **Alternatives considered**: Keep print (rejected: no levels, no severity in
  journal); structured JSON logs (rejected: overkill for one maintainer).

## R8: Testing & lint tooling — pytest + flake8 as dev-only dependencies

- **Decision**: `tests/` with pytest; offline fixtures (a saved Billboard HTML
  page, a fixture CSV, the real letter templates); no network and no SMTP in
  tests. flake8 for style (constitution names it). Dev tools live in
  `requirements-dev.txt` and do not count against the runtime dependency budget
  (SC-002 counts runtime deps).
- **Rationale**: pytest is the community standard and its fixtures keep tests
  short; unittest would work but is wordier (Principle I favors readability).
- **Alternatives considered**: stdlib unittest (rejected: more boilerplate);
  ruff instead of flake8 (rejected: constitution specifies flake8-clean; no need
  to amend it for this feature).

## R9: Python version floor

- **Decision**: Require Python ≥ 3.12; verify on 3.12 (current venv) and the
  newest stable (3.14). Use plain modern idioms (dataclasses, pathlib, `X | None`
  unions) — no 3.12-exclusive syntax is needed, the floor is set by policy and
  the constitution's constraint section gets updated from "3.10+" to "3.12+"
  after implementation lands.
- **Rationale**: Matches the user's request; after R1/R2 no dependency blocks
  3.14.

## R10: Module layout — flat modules, no package directory

- **Decision**: Keep a flat top-level layout (`main.py` entry point preserved for
  run.sh/systemd) with one module per responsibility: `config.py`,
  `recipients.py`, `charts.py`, `spotify_links.py`, `content.py`, `mailer.py`,
  plus `tests/`. Module-level side effects (the current read-config-at-import in
  three files) move into functions/constructors so importing is side-effect free
  and testable.
- **Rationale**: ~350 lines of code do not justify a src/ package hierarchy
  (Principle I); import-time side effects are what currently make the code
  untestable offline.
- **Alternatives considered**: single-file app (rejected: mixes six concerns,
  hurts testability); installable package with pyproject (rejected: nothing
  imports this project; YAGNI).
