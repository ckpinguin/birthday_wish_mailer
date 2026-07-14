# Email Output Contract

What a recipient receives. Equivalence with the legacy output is the P1
acceptance test (spec US1, SC-001).

## Envelope & headers

| Header  | Value                                                   |
| --------- | --------------------------------------------------------- |
| From    | `FROM_ADDR`                                             |
| To      | recipient email (test mode: `TEST_RECIPIENT`)           |
| Bcc     | `BCC_ADDR` when configured                              |
| Subject | `Happy Birthday!`                                       |

Transport: SMTP with STARTTLS to `MAILHOST:PORT`, authenticated as `LOGIN`.

## Body structure

Valid HTML document (UTF-8) containing, in order:

1. **Greeting text**: one of the three German letter templates, chosen at
   random, with placeholders replaced:
   - `[TITLE]` → `Liebe` (gender `f`) / `Lieber` (otherwise)
   - `[NAME]` → recipient firstname
   - `[SENDER]` → `SENDER` from config
   - Template newlines rendered as line breaks.
2. **Chart postscript** (only when chart entries exist): the text
   "P.S. Die 3 Top-Songs der US-Charts am `<d.m.yyyy>` waren:" followed by the
   YouTube hint line and a bulleted list of up to three entries
   "Song: `<title>`, Interpret: `<artist>`" — each hyperlinked to its Spotify
   URL when available, plain text otherwise.
3. **Inline image**: one of the three birthday PNGs, embedded (CID reference,
   not a remote link), displayed after the text.

## Explicitly allowed deviations from legacy bytes

- Malformed markup in the legacy composer (unclosed `</p`, stray tags) is
  corrected; rendered appearance in common mail clients stays the same or
  improves (FR-001).
- MIME structure may differ (modern `EmailMessage` multipart/related layout) as
  long as text, links, and inline image render equivalently.

## Degradation rules (FR-003)

| Condition                              | Postscript outcome                  |
| ---------------------------------------- | ------------------------------------- |
| Birth year < 1958                      | omitted                             |
| Chart fetch/parse fails                | omitted                             |
| Fewer than 3 chart entries parsed      | list shortened to what was parsed   |
| Spotify token/search fails for a song  | entry shown without hyperlink       |

In every case above the greeting text and image are still sent.
