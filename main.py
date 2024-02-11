from email.message import EmailMessage
import smtplib
import json
from typing import Sequence
import pandas
import random
import datetime as dt
import socks
from billboard_timemachine import BillboardTimeMachine
from spotifier import Spotifier
import argparse


try:
    with open(".secret.json", "r") as config_file:
        config_data: dict = json.load(config_file)
except FileNotFoundError:
    print("ERROR: No config file found!")
    exit(0)

BIRTHDAY_FILE = "birthdays.csv"
BIRTHDAY_TEST_FILE = "TEST_birthdays.csv"
TEST_MODE = False

TEST_RECIPIENT = config_data["TEST_RECIPIENT"]
SPOTIFY_CLIENT_ID = config_data["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = config_data["SPOTIFY_CLIENT_SECRET"]
SENDER = config_data.get("SENDER")
LOGIN = config_data.get("LOGIN")
MY_PASS = config_data.get("PASSWORD")
FROM_ADDR = config_data.get("FROM_ADDR")
BCC_ADDR = config_data.get("BCC_ADDR")
PORT = config_data.get("PORT")
HOSTNAME = config_data.get("MAILHOST")
PROXY = config_data.get("PROXY_HOST", None)
PROXY_PORT = config_data.get("PROXY_PORT", None)
if PROXY is not None and PROXY_PORT is not None:
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, PROXY, PROXY_PORT)
    socks.wrapmodule(smtplib)


def filter_active(df: pandas.DataFrame) -> pandas.DataFrame:
    return df[df['active'] == 1]


def filter_has_email(df: pandas.DataFrame) -> pandas.DataFrame:
    return df.dropna(subset=['email'])


def filter_has_birthday(df: pandas.DataFrame) -> pandas.DataFrame:
    return df.dropna(subset=['year', 'month', 'day'])


def filter_birthday_match(df: pandas.DataFrame,
                          month, day) -> pandas.DataFrame:
    return df.loc[(df['month'] == month) & (df['day'] == day)]


def extract_fields(df: pandas.DataFrame) -> list[dict]:
    return [{'firstname': row['firstname'],
             'gender': row['gender'], 'email': row['email'],
             'year': int(row['year']), 'month': int(row['month']),
             'day': int(row['day'])}
            for _, row in df.iterrows()]


def find_persons_with_birthday_today(file: str) -> list[dict]:
    # Looks quite verbose, but it's easier to understand and adapt:
    df_all = pandas.read_csv(file)
    df_active = filter_active(df_all)
    df_has_email = filter_has_email(df_active)
    df_birthday_exists = filter_has_birthday(df_has_email)
    now = dt.datetime.now()
    current_month = now.month
    current_day = now.day
    df_birthday_match = filter_birthday_match(
        df_birthday_exists, current_month, current_day)
    persons_that_have_birthday = extract_fields(df_birthday_match)
    return persons_that_have_birthday


def read_random_template() -> str:
    rand_no = random.randint(1, 3)
    template = f"letter_templates/letter_{rand_no}.txt"
    with open(template) as file:
        content = file.read()
    return content


def replace_content(content: str, name_to_insert: str, gender: str) -> str:
    placeholder_name = '[NAME]'
    placeholder_title = '[TITLE]'
    placeholder_sender = '[SENDER]'
    if gender == 'f':
        title = "Liebe"
    else:
        title = "Lieber"

    content_new = content.replace(placeholder_name, name_to_insert)
    content_new = content_new.replace(placeholder_title, title)
    content_new = content_new.replace(placeholder_sender, SENDER)
    return content_new


def send_mail(email_addr: str, content: str, bcc: str | None) -> None:
    print(f"Sending mail to {email_addr} from {FROM_ADDR}")

    with smtplib.SMTP(host=HOSTNAME, port=PORT) as connection:
        connection.starttls()
        connection.login(LOGIN, MY_PASS)

        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = "Happy Birthday!"
        msg["From"] = FROM_ADDR
        msg["To"] = email_addr
        if bcc:
            msg["Bcc"] = bcc
        connection.send_message(msg)


def get_special_content(top_three_songs_for_birthday: list[tuple],
                        spotify_urls: list[str]) -> str:
    content_special = "\n\nP.S. Die 3 Top-Songs der US-Charts an deinem Geburtsdatum waren:\n"
    content_special += "(Falls du kein Spotify hast, kannst du die Songs sehr leicht auf <a href='www.youtube.com'>YouTube</a> suchen)\n\n"
    i = 0
    for song, artist in top_three_songs_for_birthday:
        content_special += \
            f"Song: {song}, Interpret: {artist}: {spotify_urls[i]}\n"
        i += 1
    return content_special


def send_birthday_mail(
        person: dict,
        top_three_songs_for_birthday: list[tuple],
        spotify_urls: list[str]) -> None:
    template_content = read_random_template()
    content = replace_content(
        template_content, person['firstname'], person['gender'])

    if top_three_songs_for_birthday:
        content += "\n" + \
            get_special_content(top_three_songs_for_birthday, spotify_urls)
    if TEST_MODE:
        print(f"TEST MODE: Sending to test recipient {TEST_RECIPIENT}")
        send_mail(TEST_RECIPIENT, content, bcc=BCC_ADDR)
    else:
        send_mail(person['email'], content, bcc=BCC_ADDR)


def get_billboard_top_three_for_date(year: int,
                                     month: int,
                                     day: int) -> list[tuple]:
    year = str(year)
    month = str(month).zfill(2)
    day = str(day).zfill(2)
    billboard = BillboardTimeMachine(
        f"{year}-{month}-{day}")
    top_three_songs_for_date = billboard.get_top_three_artists_and_tracks()
    return top_three_songs_for_date


def main():
    global TEST_MODE, BIRTHDAY_FILE
    parser = argparse.ArgumentParser(
        'Send birthday emails with some extras :-)')
    parser.add_argument(
        '-t', '--test',   help='Use test CSV input file instead of real file  and send all mails to a test address (defined in .secret.json)', action='store_true')
    args = parser.parse_args()
    if args.test:
        BIRTHDAY_FILE = BIRTHDAY_TEST_FILE
        TEST_MODE = True

    persons_with_birthday = find_persons_with_birthday_today(BIRTHDAY_FILE)

    for person in persons_with_birthday:
        print(f"Getting data for {person}")
        year, month, day = person['year'], person['month'], person['day']
        billboard_entries = []
        spotify_urls = []
        if year < 1958:
            print(
                f"Year of birth is before billboard charts started. No special content will be added.")
            billboard_entries = []
            spotify_urls = []
        else:
            billboard_entries = get_billboard_top_three_for_date(
                year, month, day)
            # Spotifier constructor expects two lists, so we need to unpack the zipped tuple-list:
            spotify = Spotifier(*zip(*billboard_entries))
            spotify_urls = spotify.get_spotify_urls()

        send_birthday_mail(
            person,
            billboard_entries,
            spotify_urls=spotify_urls)


# ___ MAIN ____
if __name__ == "__main__":
    main()
