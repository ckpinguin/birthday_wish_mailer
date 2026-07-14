# CLI Contract: birthday_wish_mailer

The only external interface. Consumed by `run.sh`, the systemd service, and the
maintainer directly. This contract is frozen — `run.sh` and the systemd units
must keep working without modification.

## Invocation

```text
python main.py [-t | --test]
```

| Flag         | Effect                                                            |
| -------------- | ------------------------------------------------------------------- |
| (none)       | Read `birthdays.csv`, send to real recipients                     |
| `-t, --test` | Read `TEST_birthdays.csv`, send every mail to the test recipient  |

## Files read (relative to working directory = repo root)

- `.secret.json` — configuration (see data-model.md → AppConfig)
- `birthdays.csv` or `TEST_birthdays.csv`
- `letter_templates/letter_{1..3}.txt`
- `images/small_bday{1..3}.png`

## Exit codes

| Code | Meaning                                                            |
| ------ | -------------------------------------------------------------------- |
| 0    | Run completed; all due mails sent (including "no birthdays today") |
| 1    | Fatal: config/data file missing or invalid — nothing was attempted |
| 2    | Partial failure: at least one due recipient did not get their mail |

(Change from legacy behavior: missing config used to exit 0. Codes 1/2 make
systemd surface failures — FR-004, FR-008.)

## Log output (stdout, captured by journald)

Per run, at minimum (FR-009):

```text
INFO matched N recipient(s): <names>            | or: INFO no birthdays today
INFO charts for 1994-03-12: ok (3 entries)      | WARNING charts for …: <error> — sending without extras
INFO spotify link for '<title>': ok             | WARNING spotify link for '<title>': <error>
INFO sent mail to <address>                     | ERROR send to <address> failed: <error>
```

No credentials and no full recipient list dumps appear in logs; only the data
needed to trace the run (Principle II + V).
