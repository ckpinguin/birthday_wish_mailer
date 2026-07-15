# Contract: Review Email

The message delivered to the owner for every due birthday. Supersedes the
recipient-visible mail contract of feature 001
([email-output.md](../../001-modernize-codebase/contracts/email-output.md))
**only** in headers and the prepended routing block — the greeting content
itself remains bound by that contract unchanged.

## Headers

| Header | Value | Notes |
| --------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| `From` | `FROM_ADDR` (unchanged) | |
| `To` | real run: `OWNER_RECIPIENT` · test run: test recipient | never the birthday person's address, in any mode (FR-001) |
| `Bcc` | `BCC_ADDR` if configured (unchanged) | research R6 |
| `Subject` | `Geburtstagsmail für {firstname} ({email})` | `{email}` = birthday person's address; same format in both modes (FR-005, R4, R5) |

## Body structure (HTML, single alternative part as today)

```html
<html><head><meta charset="utf-8"></head><body>
  <!-- 1. routing block: NEW, always first -->
  <div style="border: 2px dashed #888888; background: #f2f2f2;
              padding: 8px 12px; margin-bottom: 16px;
              font-family: monospace;">
    Für: {firstname} &lt;{email}&gt;<br>
    Diesen Kasten vor dem Weiterleiten entfernen.
  </div>
  <!-- 2. greeting: UNCHANGED from feature 001 contract -->
  <p>{greeting with placeholders filled}</p>
  {optional chart postscript}
  <p><img src="cid:birthday-image"></p>
</body></html>
```

Rules:

- Routing block is always the first element in `<body>` (research R3).
- `{firstname}` and `{email}` are HTML-escaped; the address appears as
  selectable plain text — no `mailto:` link, no image (FR-004).
- All styling on the routing block is inline CSS (mail-client compatibility);
  visual separation (border + background) is mandatory (FR-007).
- Everything after the routing block is byte-identical to the pre-feature
  body: same greeting HTML, same postscript rules, same CID image (FR-006).
  The graceful-degradation table from the 001 contract still governs the
  greeting part (Principle IV).
- The routing block is core content, not enrichment: it must never be
  omitted. (Its inputs come from the CSV row, which is guaranteed non-empty
  by the loader's filtering.)

## Cardinality

One review email per due birthday person per run — N due birthdays produce
exactly N messages to the owner, never a digest (SC-001, spec edge case).

## Log contract (per send, stdout → journald)

```text
INFO sent mail for {firstname} (intended: {email}) to {delivery_addr}
ERROR send for {firstname} (intended: {email}) failed: {reason}
```

Both the intended birthday person and the actual delivery address must
appear on success and failure lines (FR-009, research R7).
