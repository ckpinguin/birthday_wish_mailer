# Contract: Song Links in the P.S. Block

Delta against the feature-001 email contract
([email-output.md](../../001-modernize-codebase/contracts/email-output.md))
and orthogonal to feature 002's review-email contract (routing block and
subject are untouched). Only the `href` targets inside the chart P.S.
change.

## Link format

```text
https://open.spotify.com/search/<ENCODED>
ENCODED = percent-encoding of "<title> <artist>" as ONE path segment
          (space → %20; &, /, ?, #, ', non-ASCII → %XX; nothing left "safe")
```

Examples:

| Song | Link |
| ------------------------------------ | ------------------------------------------------------------------------ |
| `Hey Jude` — `The Beatles` | `https://open.spotify.com/search/Hey%20Jude%20The%20Beatles` |
| `AM/FM` — `X & Y` | `https://open.spotify.com/search/AM%2FFM%20X%20%26%20Y` |

Rules:

- Built for **every** fetched chart entry; no lookup, no network call, no
  credential involved (FR-001, FR-002).
- The encoded URL contains no raw `&`, `<`, `>` or quotes, so it is
  HTML-safe verbatim inside the existing `<a href="...">` template — the
  P.S. markup itself must not change (FR-004).
- The visible list item text (`Song: …, Interpret: …`) and the YouTube hint
  are byte-identical to today (FR-004).

## Degradation ladder (unchanged from 001, restated)

| Condition | Result |
| ------------------------------------ | ---------------------------------------------- |
| birth year < 1958 | no P.S. block, greeting sent |
| chart fetch/parse fails | no P.S. block, greeting sent, warning logged |
| entry without link (defensive `None`) | song listed as plain text, greeting sent |

Link building itself has no failure branch — it is pure string
construction (research R4); nothing new may abort a send (FR-006).

## Log delta (Principle V)

Removed lines (events that no longer exist): `spotify link for '…': ok/no
match`, `… sending song list without links` (token failure). Unchanged:
chart-fetch logging and feature 002's per-send `sent mail for … (intended:
…) to …` lines.
