# Contract: CLI & Configuration Delta

Delta against the frozen feature-001 contracts
([cli.md](../../001-modernize-codebase/contracts/cli.md),
[data-files.md](../../001-modernize-codebase/contracts/data-files.md)).
Everything not listed here is unchanged: invocation flags, files read, CSV
format, templates, images, `run.sh`, systemd units.

## Invocation semantics (flags unchanged)

| Mode | Before this feature | After this feature |
| ------------ | ------------------------------------------ | ----------------------------------------------------------------- |
| *(none)* | send to each birthday person's address | send every mail to `OWNER_RECIPIENT`; review format (routing block + labeled subject) |
| `-t, --test` | send everything to test recipient | unchanged delivery; same review format as real mode (FR-008) |

Direct-to-recipient delivery no longer exists in any mode (spec assumption:
permanent redirection, not an optional mode).

## `.secret.json` delta

| Key | Required? | Meaning |
| ----------------- | ------------------------------ | ------------------------------------------------------ |
| `OWNER_RECIPIENT` | for real runs (new key) | delivery address for all review emails in real mode |
| all existing keys | unchanged | unchanged (incl. `TEST_RECIPIENT`/`BCC_ADDR` fallback) |

The key stays out of the repo like every other secret (Principle II);
README documents it with a placeholder address only.

## Exit codes (values unchanged, one new trigger for `1`)

| Code | Meaning |
| ---- | ------------------------------------------------------------------------------------------ |
| 0 | run completed; all due review mails delivered (including "no birthdays today") |
| 1 | fatal startup problem — **now also**: real run without `OWNER_RECIPIENT` (FR-003); occurs before any send, zero mails go out |
| 2 | partial failure: at least one review mail was not delivered to the owner |

## Startup log for the new failure

```text
ERROR cannot start: real mode needs OWNER_RECIPIENT in .secret.json
```

Mirrors the existing test-mode message style so journald triage stays
uniform (Principle V, SC-004).
