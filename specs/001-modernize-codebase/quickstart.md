# Quickstart Validation: Modernize Codebase

Runnable checks proving the refactor meets the spec. Run from the repo root.

## Prerequisites

- Python ≥ 3.12 available (`python3 --version`)
- `.secret.json`, `birthdays.csv`, `TEST_birthdays.csv` present (untracked)
- `TEST_birthdays.csv` contains at least one active row born ≥ 1958 with
  month/day = today, and one born < 1958 (edit dates before testing)

## 1. Fresh environment installs (SC-003)

```sh
rm -rf .venv && PYTHON=python3.12 ./run.sh --help   # bootstraps venv, prints usage
.venv/bin/pip install -r requirements-dev.txt
```

Expected: no errors; `pip list` shows only requests + beautifulsoup4 (and
transitives) as runtime deps. Repeat with the newest stable Python
(`PYTHON=python3.14`) on a scratch copy.

## 2. Offline check suite (SC-005, FR-011, FR-012)

```sh
.venv/bin/python -m pytest
.venv/bin/python -m flake8 .
```

Expected: all tests pass in < 1 min, zero network calls, zero mails sent,
flake8 silent with no `# noqa` in the codebase. Negative check: break a
placeholder replacement locally → at least one test fails naming composition.

## 3. Behavior preservation — test send (SC-001, US1; Constitution III)

```sh
./run.sh --test
```

Expected in the test-recipient inbox (one mail per matching test row):

- born ≥ 1958: German greeting (correct salutation), inline image, P.S. block
  with 3 chart songs as clickable Spotify links
- born < 1958: greeting + image, no P.S. block

Compare side by side against a legacy mail per
[contracts/email-output.md](contracts/email-output.md).

## 4. Graceful degradation (SC-004, US2)

Simulate chart failure (e.g., point the chart URL constant at an unreachable
host in a scratch copy, or disconnect network after config load) and run
`./run.sh --test`.

Expected: greeting mails still arrive without the P.S. block; log contains a
WARNING naming the chart failure; exit code 0.

## 5. Failure visibility (FR-004, FR-008)

```sh
mv .secret.json .secret.json.bak && ./run.sh --test; echo "exit: $?"; mv .secret.json.bak .secret.json
```

Expected: clear error naming the missing config, exit code 1 (systemd would
show the unit as failed).

## 6. Scheduled-run observability (SC-006)

After a `--test` run: the log alone answers "who matched" and "what was sent to
whom" per the format in [contracts/cli.md](contracts/cli.md). On the
homeserver: `journalctl -u birthday-mailer.service`.
