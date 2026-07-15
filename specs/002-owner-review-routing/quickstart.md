# Quickstart: Validating Owner Review Routing

Run these scenarios in order after implementation. Scenarios 1–4 are safe by
construction; scenario 5 touches real mode and must be done exactly as
written. Contract details: [contracts/](contracts/); field rules:
[data-model.md](data-model.md).

## Prerequisites

- Working `.secret.json` (see feature-001
  [data-files contract](../001-modernize-codebase/contracts/data-files.md))
  — scenario 2 adds the new key
- `TEST_birthdays.csv` containing at least one active row whose month/day
  match today (edit a row if needed)
- Dev venv with `requirements-dev.txt` installed

## 1. Offline checks (no network, no mail)

```sh
.venv/bin/python -m pytest
.venv/bin/python -m flake8 .
```

**Expected**: all tests pass (including the new routing-block, subject, and
config tests), flake8 silent.

## 2. Configure the new key

Add to `.secret.json` (your own address — this is where all real birthday
mail will land from now on):

```json
"OWNER_RECIPIENT": "you@example.com"
```

## 3. Test send — review format verification (Principle III gate)

```sh
./run.sh --test
```

**Expected** in the test recipient's inbox, per due row in the test CSV:

- one email per birthday person, subject
  `Geburtstagsmail für {firstname} ({email})`
- routing block first: dashed grey box, name + address as selectable plain
  text, removal hint — clearly not part of the letter
- greeting below it renders exactly as before the feature (salutation,
  text, chart P.S. when applicable, inline image)
- log line per send:
  `sent mail for {firstname} (intended: {email}) to {test_recipient}`

## 4. Forward rehearsal (the actual workflow)

In your mail client, forward one received review email to the test
recipient address: delete the routing block, add a personal sentence, set a
normal subject, send.

**Expected**: the forwarded copy renders the greeting correctly with your
added line and shows no trace of the routing block. This proves SC-003
(review → personalize → forward, no reformatting).

## 5. Real-mode startup guard (safe negative test)

Temporarily remove/rename the `OWNER_RECIPIENT` key from `.secret.json`,
then:

```sh
./run.sh ; echo "exit: $?"
```

**Expected**: `ERROR cannot start: real mode needs OWNER_RECIPIENT in
.secret.json`, `exit: 1`, **zero mails sent** (the guard fires before any
send — this is what makes the test safe even with real birthdays today).
Restore the key afterwards and confirm `./run.sh --test` works again.

## 6. First unattended real run

After deploying, on the next timer run check the journal:

```sh
journalctl -u birthday-mailer.service -n 50
```

**Expected**: for each due birthday, a `sent mail for … (intended: …) to
{OWNER_RECIPIENT}` line; the review mail(s) in the owner inbox; **no mail at
any birthday person's address** (SC-001). Then do the real forward — that
part stays manual by design.
