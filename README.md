# Birthday Reminder

Since I'm so bad at remembering b'days and my proton calendar does not yet support a useful API and does not even show b'days on calendar, I had to find my own solution.

## Requirements

- Python 3.10 – 3.12 (the pinned pandas/numpy versions in `requirements.txt`
  don't have wheels for newer Pythons yet)
- The following files in the repo root — they are **gitignored on purpose**
  (secrets / personal data), so copy them to the server manually:
  - `.secret.json` with the keys `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
    `SENDER`, `BCC_ADDR`, `LOGIN`, `PASSWORD`, `FROM_ADDR`, `PORT`, `MAILHOST`
    and optionally `PROXY_HOST`, `PROXY_PORT`
  - `birthdays.csv` and `TEST_birthdays.csv` with the columns
    `firstname,gender,email,year,month,day,active`

## Running it

`run.sh` creates the venv on first use (installing `requirements.txt`) and then
runs the app through it, so this is all you need:

```sh
./run.sh --test   # sends to the test recipient from .secret.json — always try this first
./run.sh          # the real thing
```

If your default `python3` is too new, point the bootstrap at another
interpreter once: `PYTHON=python3.12 ./run.sh --test`

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
0 8 * * * /home/chris/birthday_wish_mailer/run.sh >> /home/chris/birthday_wish_mailer/mailer.log 2>&1
```
