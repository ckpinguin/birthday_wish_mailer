# Birthday Reminder

Since I'm so bad at remembering b'days and my proton calendar does not yet support a useful API and does not even show b'days on calendar, I had to find my own solution.

## Requirements

- Python 3.12 or newer
- The following files in the repo root — they are **gitignored on purpose**
  (secrets / personal data), so copy them to the server manually:
  - `.secret.json` with the keys `SENDER`, `LOGIN`, `PASSWORD`, `FROM_ADDR`,
    `PORT`, `MAILHOST`, `OWNER_RECIPIENT` (your own address — all real
    birthday mail goes there for review, see below) and optionally
    `BCC_ADDR`, `TEST_RECIPIENT` (test mails go there; falls back to
    `BCC_ADDR`). No Spotify credentials or developer account are needed —
    song links point to Spotify search results, built without any API call.
  - `birthdays.csv` and `TEST_birthdays.csv` with the columns
    `firstname,gender,email,year,month,day,active`

### Dependencies

Only two runtime libraries (everything else is standard library):

- `requests` — HTTP client for the Billboard chart page; de-facto standard,
  clearer than stdlib `urllib`
- `beautifulsoup4` — robust CSS-selector parsing of the Billboard chart page;
  hand-rolled HTML parsing would be brittle and unreadable

Dev-only tools live in `requirements-dev.txt` (`pytest`, `flake8`):

```sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest      # offline test suite (no mails, no network)
.venv/bin/python -m flake8 .    # style check
```

## Running it

`run.sh` creates the venv on first use (installing `requirements.txt`) and then
runs the app through it, so this is all you need:

```sh
./run.sh --test   # sends to the test recipient from .secret.json — always try this first
./run.sh          # the real thing
```

If your default `python3` is too new, point the bootstrap at another
interpreter once: `PYTHON=python3.12 ./run.sh --test`

## Review-and-forward workflow

The app never mails a birthday person directly. Every generated greeting is
delivered to `OWNER_RECIPIENT` (e.g. `you@example.com`) so you can add a
personal touch first:

1. On a birthday, you receive one mail per person, subject
   `Geburtstagsmail für <name> (<address>)`.
2. The mail starts with a grey dashed box naming the intended recipient;
   below it sits the finished greeting exactly as they should see it.
3. Forward the mail: delete the grey box, add your personal line, set a
   normal subject, and send it to the address from the box.

A real run without `OWNER_RECIPIENT` in `.secret.json` stops with an error
before sending anything (exit code 1). Test runs (`--test`) still deliver to
`TEST_RECIPIENT`, using the same review layout.

## Daily run on the homeserver (systemd timer)

A systemd timer is used instead of a cronjob because `Persistent=true` catches
up on missed runs after downtime (cron would silently skip the birthday), and
logs land in journald.

```sh
sudo cp deploy/birthday-mailer.service deploy/birthday-mailer.timer /etc/systemd/system/
sudo nano /etc/systemd/system/birthday-mailer.service   # adjust User= and the two paths
sudo systemctl daemon-reload
sudo systemctl enable --now birthday-mailer.timer
```

Check that it's scheduled and see the logs of past runs:

```sh
systemctl list-timers birthday-mailer.timer
journalctl -u birthday-mailer.service
```

The timer fires daily at 08:00 (edit `OnCalendar=` in the timer to taste).
To trigger a real run immediately: `sudo systemctl start birthday-mailer.service`
— but run `./run.sh --test` first after any change to templates or mail code.

### Cron alternative

If you prefer plain cron, this line does the same minus the catch-up behavior:

```text
0 8 * * * /home/<USER>/birthday_wish_mailer/run.sh >> /home/<USER>/birthday_wish_mailer/mailer.log 2>&1
```
