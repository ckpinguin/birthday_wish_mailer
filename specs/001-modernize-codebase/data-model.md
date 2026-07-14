# Data Model: Modernize Codebase

## Recipient

One row of `birthdays.csv` / `TEST_birthdays.csv`.

| Field     | Type            | Rules                                            |
| ----------- | ----------------- | -------------------------------------------------- |
| firstname | str             | Used for `[NAME]` placeholder                    |
| gender    | str (`"f"`/`"m"`) | `"f"` → salutation "Liebe", otherwise "Lieber" |
| email     | str             | Recipient address (real mode)                    |
| year      | int             | Birth year; `< 1958` → no chart enrichment       |
| month     | int             | 1–12                                             |
| day       | int             | 1–31                                             |
| active    | int (`0`/`1`)   | Only `1` is processed                            |

**Selection rules** (all must hold, matching current behavior — FR-002):
`active == 1` AND `email` non-empty AND `year`, `month`, `day` all present/parsable
AND `month == today.month` AND `day == today.day`.

Rows failing any rule are skipped silently (as today); a row with unparsable
numeric fields is skipped with a warning log line (replaces today's crash).

## AppConfig

Contents of `.secret.json` (untracked, Principle II). Loaded once at startup;
missing required key → fatal error, exit 1 (FR-008).

| Key                   | Required | Purpose                                        |
| ----------------------- | ---------- | ------------------------------------------------ |
| MAILHOST              | yes      | SMTP host                                      |
| PORT                  | yes      | SMTP port (STARTTLS)                           |
| LOGIN                 | yes      | SMTP username                                  |
| PASSWORD              | yes      | SMTP password                                  |
| FROM_ADDR             | yes      | From header                                    |
| SENDER                | yes      | `[SENDER]` placeholder in greeting text        |
| BCC_ADDR              | no       | Bcc on every mail                              |
| TEST_RECIPIENT        | no       | Test-mode recipient; falls back to BCC_ADDR    |
| SPOTIFY_CLIENT_ID     | yes      | Spotify Client Credentials                     |
| SPOTIFY_CLIENT_SECRET | yes      | Spotify Client Credentials                     |

Removed (dead, R4): `PROXY_HOST`, `PROXY_PORT`.

## ChartEntry

One of the top-3 Billboard Hot 100 entries for the recipient's birth date.

| Field       | Type        | Rules                                             |
| ------------- | ------------- | --------------------------------------------------- |
| title       | str         | From chart page                                   |
| artist      | str         | From chart page                                   |
| spotify_url | str \| None | First search hit; None → entry listed without link |

A recipient's enrichment is `list[ChartEntry]` (0–3 entries). Empty list (birth
year < 1958, fetch/parse failure) → greeting without postscript (FR-003).

## Greeting (composed email)

| Part       | Source                                                        |
| ------------ | --------------------------------------------------------------- |
| Subject    | Fixed: `Happy Birthday!`                                      |
| Body HTML  | Random template from `letter_templates/letter_{1..3}.txt` with `[NAME]`, `[TITLE]`, `[SENDER]` replaced; newlines → `<br>`; valid HTML document (R5) |
| Postscript | Rendered from `list[ChartEntry]` when non-empty               |
| Image      | Random `images/small_bday{1..3}.png`, embedded inline via CID |
| To         | Recipient email (real) / TEST_RECIPIENT (test mode)           |
| Bcc        | BCC_ADDR when set                                             |

## Relationships & flow

```text
AppConfig ──────────────┐
birthdays.csv → [Recipient] → per recipient:
                              year ≥ 1958 → ChartEntry×3 (best effort)
                              template + image + entries → Greeting → SMTP send
```

No persistent state; every run is stateless and idempotent for the day it runs.
