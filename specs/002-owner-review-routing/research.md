# Research: Owner Review Routing

All Technical Context unknowns resolved. Decisions numbered R1–R7 and
referenced from plan.md, data-model.md, and the contracts.

## R1: Where the redirection happens

- **Decision**: In the orchestration layer (`main.run`), exactly where the
  test-mode redirection already lives: the delivery address becomes
  `OWNER_RECIPIENT` in real mode and stays the test recipient in test mode.
  The birthday person's address is passed onward as display data only.
- **Rationale**: `main.run` already owns the "who actually gets the mail"
  decision (`to_addr = test_recipient if test_mode else person.email`); this
  feature changes one leg of that expression. Redirecting inside `mailer.py`
  would hide routing policy in the transport layer and make the mailer read
  config it otherwise doesn't need (Principle I: explicit, step-by-step
  logic).
- **Alternatives considered**: (a) override inside `mailer.send_greeting` —
  rejected: mailer stays a dumb transport, policy stays visible in `run()`;
  (b) rewrite `Recipient.email` after CSV load — rejected: mutating loaded
  data to express routing is exactly the kind of clever indirection the
  constitution forbids, and the real address must survive as display data.

## R2: How `OWNER_RECIPIENT` enters the configuration

- **Decision**: New optional key in `.secret.json`, loaded into
  `AppConfig.owner_recipient: str | None` (default `None`). `main.run`
  validates it at startup for real runs only: missing/empty → log a clear
  error, exit 1, before any CSV row is processed into a send.
- **Rationale**: Mirrors the existing `TEST_RECIPIENT` pattern (optional key,
  mode-specific startup validation in `run()` with exit code 1). Keeping it
  out of `REQUIRED_KEYS` means a `--test` run still works before the owner
  has updated their server-side `.secret.json`, which is the order in which
  the rollout will actually happen (Principle III: test first).
- **Alternatives considered**: adding it to `REQUIRED_KEYS` — rejected: would
  break `--test` runs on not-yet-updated configs and couples test mode to a
  key it never uses; silent fallback to direct sending when missing —
  rejected explicitly by the spec (edge case: "a silent fallback to direct
  sending would defeat the feature's purpose").

## R3: Routing information placement — inline block, not attachment

- **Decision**: A visually separated routing block at the **top** of the HTML
  body, above the greeting: a dashed-border, grey-background `<div>` with
  inline CSS containing the intended recipient's first name and email address
  as plain text (HTML-escaped), plus a one-line German hint to remove the
  block before forwarding. The greeting below it stays byte-identical to what
  the mailer produces today.
- **Rationale**: The spec already fixed inline-over-attachment (delegated
  decision, recorded in spec Assumptions). Top placement means the owner sees
  the destination before the greeting when opening the mail, and a single
  contiguous block at the top is the easiest thing to delete in a
  forward-compose window. Inline CSS is required anyway because mail clients
  ignore `<style>` blocks inconsistently. Grey/dashed styling makes it
  visually "not part of the letter" (FR-007).
- **Alternatives considered**: (a) `.eml`/`.html` attachment — rejected by
  spec; (b) custom `X-Intended-Recipient` header only — rejected: invisible
  in normal mail clients, fails FR-004; (c) routing info below the greeting —
  rejected: easy to overlook and harder to trim when forwarding; (d) a
  `mailto:` link instead of plain text — rejected: plain text is the
  copyable requirement (FR-004); a link adds nothing the owner's client
  doesn't already offer and some clients make link text harder to copy.

## R4: Subject line format

- **Decision**: `Geburtstagsmail für {firstname} ({email})` replaces the
  fixed `Happy Birthday!` subject on the review email.
- **Rationale**: FR-005 requires the inbox list alone to distinguish
  same-day birthday mails; the name does that, and carrying the address in
  the subject makes the destination visible without even opening the mail.
  German matches the letter templates and the owner's mail context. The
  final recipient never sees this subject — the owner composes or rewrites
  the subject when forwarding (subject editing is trivial in every client,
  unlike body editing, so the friction sits in the right place).
- **Alternatives considered**: keeping `Happy Birthday!` — rejected: fails
  FR-005 with multiple birthdays and makes the review mail look like a mail
  *to* the owner; `Happy Birthday, {firstname}!` without address — rejected:
  satisfies distinguishability but wastes the chance to satisfy "address
  visible from the inbox list" and looks forward-ready when it isn't.

## R5: Test mode behavior

- **Decision**: Test mode is unchanged in delivery (test CSV, all mail to
  `TEST_RECIPIENT`/`BCC_ADDR` fallback) but carries the identical review
  format — routing block and new subject — unconditionally.
- **Rationale**: FR-008 and Principle III: the thing `--test` must let the
  owner verify is now the review email itself, so the formatting must not
  branch on mode. Implementation-wise the formatting becomes unconditional
  and only the delivery address differs, which is less code, not more.
- **Alternatives considered**: test mode keeping the old direct format —
  rejected: the new layout could then never be verified before a real run,
  violating Principle III.

## R6: BCC behavior

- **Decision**: Unchanged — `BCC_ADDR`, when set, is still added to every
  outgoing message.
- **Rationale**: Spec assumption freezes it. If `BCC_ADDR` equals
  `OWNER_RECIPIENT` the SMTP server delivers one copy to one mailbox; no
  harm. Removing the Bcc conditionally would add a mode branch for zero
  user-visible benefit (Principle I).
- **Alternatives considered**: dropping Bcc on review mails — rejected as
  speculative cleanup outside the feature's scope.

## R7: Log line format for intended vs. actual recipient

- **Decision**: The per-send success log names both parties, e.g.
  `sent mail for Anna (intended: anna@example.org) to owner@example.com`;
  send-failure logs likewise name the birthday person being processed, not
  just the delivery address.
- **Rationale**: FR-009 / Principle V: after this feature, "who the mail was
  for" and "where it went" are different facts, and both must be
  reconstructable from journald alone. The existing
  `log.info("sent mail to %s", to_addr)` line loses the first fact.
- **Alternatives considered**: leaving the log format alone — rejected: a
  failed send would be attributed only to the owner's address, making it
  impossible to tell from logs whose birthday mail is missing.
