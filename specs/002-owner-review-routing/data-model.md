# Data Model: Owner Review Routing

Small feature, small model: one extended entity, one reinterpreted entity,
one new composed artifact. Types refer to the existing flat modules
(see plan.md → Project Structure).

## AppConfig (extended) — `config.py`

| Field | Type | Source key | Rules |
| ------------------ | ------------- | ----------------- | ------------------------------------------------------------------ |
| *(existing fields)* | *(unchanged)* | *(unchanged)* | mailhost, port, login, password, from_addr, sender, spotify_*, bcc_addr, test_recipient |
| `owner_recipient` | `str \| None` | `OWNER_RECIPIENT` | Optional at load time (like `TEST_RECIPIENT`). **Real runs**: must be non-empty; `main.run` fails with exit 1 before any send if missing (FR-003, research R2). **Test runs**: not consulted. |

State transitions: none — config remains an immutable snapshot per run.

## Recipient (unchanged fields, changed role) — `recipients.py`

| Field | Change |
| ----------- | -------------------------------------------------------------------------------------------- |
| `email` | No longer a delivery target in any mode. Becomes display data on the review email (routing block + subject) and log data (research R7). |
| all others | Unchanged; loading, `active`-flag filtering, and `due_today` selection rules untouched. |

Rows without a valid email are still skipped at load time, so every review
email always has a non-empty intended address to display (spec edge case).

## ReviewEmail (new composed artifact) — assembled by `main.py` from `content.py` + `mailer.py`

Not a class — the feature stays with plain functions (Principle I). This is
the shape of the message handed to SMTP; the authoritative field-level
contract is [contracts/review-email.md](contracts/review-email.md).

| Part | Value | Produced by |
| ------------- | ------------------------------------------------------------------------ | ------------------------------------- |
| To | `OWNER_RECIPIENT` (real) / test recipient (test) | `main.run` picks (research R1, R5) |
| Bcc | `BCC_ADDR` if set (unchanged) | `mailer.build_message` (R6) |
| Subject | `Geburtstagsmail für {firstname} ({email})` | new `content` helper (R4) |
| Routing block | dashed grey `<div>`: name + address as escaped plain text + removal hint | new `content.render_routing_block` (R3) |
| Greeting body | existing greeting HTML — byte-identical to pre-feature output | existing `content` functions (FR-006) |
| Inline image | existing CID-embedded PNG (unchanged) | `mailer.build_message` |

**Invariant**: stripping the routing block and the subject from a
ReviewEmail yields exactly the message the birthday person would have
received before this feature (FR-006).

## Validation rules recap

1. `OWNER_RECIPIENT` missing/empty + real run → exit 1, zero sends (FR-003).
2. Routing block content is HTML-escaped (names can contain `&`, addresses
   can contain `+` etc.; escaping keeps the block valid and copyable).
3. One ReviewEmail per due birthday person — never combined (spec edge case).
