"""Send birthday wish emails with chart extras — entry point.

Usage: python main.py [-t | --test]
Exit codes: 0 ok, 1 fatal startup problem, 2 partial send failure.
"""

import argparse
import datetime as dt
import logging
import sys

import charts
import content
import mailer
import recipients
from config import AppConfig, ConfigError, load_config
from spotify_links import search_url

BIRTHDAY_FILE = "birthdays.csv"
BIRTHDAY_TEST_FILE = "TEST_birthdays.csv"
FIRST_CHART_YEAR = 1958

log = logging.getLogger(__name__)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send birthday emails with some extras :-)")
    parser.add_argument(
        "-t", "--test", action="store_true",
        help="use the test CSV input file and send all mails to the "
             "test recipient (defined in .secret.json)")
    return parser.parse_args(argv)


def gather_chart_entries(
        person: recipients.Recipient) -> list[charts.ChartEntry]:
    """Best-effort enrichment; any failure means fewer/no extras."""
    if person.year < FIRST_CHART_YEAR:
        log.info("%s was born before %d: no chart extras",
                 person.firstname, FIRST_CHART_YEAR)
        return []
    try:
        birth_date = dt.date(person.year, person.month, person.day)
        entries = charts.fetch_top_three(birth_date)
        log.info("charts for %s: ok (%d entries)",
                 birth_date.isoformat(), len(entries))
    except (charts.ChartsError, ValueError) as exc:
        log.warning("charts lookup failed: %s - sending without extras",
                    exc)
        return []
    for entry in entries:
        entry.spotify_url = search_url(entry.title, entry.artist)
    return entries


def send_to_person(person: recipients.Recipient, config: AppConfig,
                   to_addr: str) -> None:
    entries = gather_chart_entries(person)
    template_text = content.choose_template_path().read_text(
        encoding="utf-8")
    greeting = content.fill_placeholders(
        template_text, person.firstname, person.gender, config.sender)
    birthday = f"{person.day}.{person.month}.{person.year}"
    postscript = content.render_postscript(birthday, entries)
    routing_block = content.render_routing_block(person.firstname,
                                                 person.email)
    subject = content.review_subject(person.firstname, person.email)
    html_body = content.compose_html(greeting, postscript,
                                     mailer.IMAGE_CID, routing_block)
    mailer.send_greeting(config, to_addr, subject, html_body,
                         content.choose_image_path())


def run(test_mode: bool) -> int:
    csv_file = BIRTHDAY_TEST_FILE if test_mode else BIRTHDAY_FILE
    try:
        config = load_config()
        all_recipients = recipients.load_recipients(csv_file)
    except (ConfigError, OSError) as exc:
        log.error("cannot start: %s", exc)
        return 1

    test_recipient = None
    if test_mode:
        test_recipient = config.test_recipient or config.bcc_addr
        if not test_recipient:
            log.error("cannot start: test mode needs TEST_RECIPIENT "
                      "or BCC_ADDR in .secret.json")
            return 1
    elif not config.owner_recipient:
        log.error("cannot start: real mode needs OWNER_RECIPIENT "
                  "in .secret.json")
        return 1

    due = recipients.due_today(all_recipients, dt.date.today())
    if not due:
        log.info("no birthdays today")
        return 0
    log.info("matched %d recipient(s): %s", len(due),
             ", ".join(person.firstname for person in due))

    failures = 0
    for person in due:
        # never the birthday person's address: the owner reviews and
        # forwards every greeting manually (specs/002)
        to_addr = test_recipient if test_mode else config.owner_recipient
        try:
            send_to_person(person, config, to_addr)
            log.info("sent mail for %s (intended: %s) to %s",
                     person.firstname, person.email, to_addr)
        except Exception as exc:
            log.error("send for %s (intended: %s) failed: %s",
                      person.firstname, person.email, exc)
            failures += 1
    return 2 if failures else 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format="%(levelname)s %(message)s")
    args = parse_args(argv)
    return run(args.test)


if __name__ == "__main__":
    sys.exit(main())
