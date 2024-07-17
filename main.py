
import json
import pandas
import random
import datetime as dt
from billboard_timemachine import BillboardTimeMachine
from spotifier import Spotifier
import argparse
from mailer import Mailer


BIRTHDAY_FILE = "birthdays.csv"
BIRTHDAY_TEST_FILE = "TEST_birthdays.csv"
TEST_MODE = False

try:
    with open(".secret.json", "r") as config_file:
        config_data: dict = json.load(config_file)
except FileNotFoundError:
    print("ERROR: No config file found!")
    exit(0)
SPOTIFY_CLIENT_ID = config_data["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = config_data["SPOTIFY_CLIENT_SECRET"]
SENDER = config_data.get("SENDER")
BCC_ADDR = config_data.get("BCC_ADDR")
TEST_RECIPIENT = BCC_ADDR


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
    with open(template, "r", encoding="utf-8") as file:
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


def get_special_content(                        top_three_songs_for_birthday: list[tuple],
                        spotify_urls: list[str]) -> str:
    content_special = ("<br><br>P.S. Die 3 Top-Songs der US-Charts an "
                       "Deinem Geburtsdatum waren:<br>")
    content_special += ("(Falls du kein Spotify hast, kannst du die "
                        "Songs sehr leicht auf www.youtube.com suchen)<br>")
    i = 0
    content_special += "<ul>"
    for song, artist in top_three_songs_for_birthday:
        content_special += \
            f"<li><a href='{spotify_urls[i]}'>Song: {song}, Interpret: {artist}</a></li>"
        i += 1
    content_special += "</ul>"
    return content_special


def construct_content(
        person: dict,
        top_three_songs_for_birthday: list[tuple],
        spotify_urls: list[str]) -> str:

    template_content = read_random_template()
    content = replace_content(
        template_content, person['firstname'], person['gender'])

    special_content = get_special_content(
        top_three_songs_for_birthday, spotify_urls) if\
        top_three_songs_for_birthday else ""

    content_html = f"<html><head><meta charset='UTF-8'></head><body><p>{content}</p><p>{special_content}</p></body></html>"
    content_html = content_html.replace("\n", "<br>")  # for letter
    return content_html


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


def get_content_and_send_email_to(persons: list) -> None:
    for person in persons:
        print(f"Getting data for {person}")
        year, month, day = person['year'], person['month'], person['day']
        billboard_entries = []
        spotify_urls = []
        if year < 1958:
            print(("Year of birth is before billboard charts started."
                   "No special content will be added."))
        else:
            billboard_entries = get_billboard_top_three_for_date(
                year, month, day)
            # Spotifier constructor expects two lists, so we need
            # to unpack the zipped tuple-list:
            spotify = Spotifier(*zip(*billboard_entries))
            spotify_urls = spotify.get_spotify_urls()

        content = construct_content(
            person,
            billboard_entries,
            spotify_urls=spotify_urls)
        recipient_email = TEST_RECIPIENT if TEST_MODE else person['email']
        mailer = Mailer(email_addr=recipient_email, bcc=BCC_ADDR)
        mailer.attach_image_to_mail(get_random_image_path())
        mailer.send_mail(content=content)


def get_random_image_path() -> str:
    rand_no = random.randint(1, 3)
    image_path = f"images/small_bday{rand_no}.png"
    return image_path


def main():
    global TEST_MODE, BIRTHDAY_FILE
    parser = argparse.ArgumentParser(
        'Send birthday emails with some extras :-)')
    parser.add_argument(
        '-t',
        '--test',
        help=("Use test CSV input file instead of real file and"
              "send all mails to a test address (defined in .secret.json)"),
        action='store_true')
    args = parser.parse_args()
    if args.test:
        BIRTHDAY_FILE = BIRTHDAY_TEST_FILE
        TEST_MODE = True

    persons_with_birthday = find_persons_with_birthday_today(BIRTHDAY_FILE)
    if persons_with_birthday:
        print(f"Persons with birthday today: {persons_with_birthday}")
    else:
        print("No persons with birthday today found. Exiting.")
        exit(0)
    get_content_and_send_email_to(persons_with_birthday)


# ___ MAIN ____
if __name__ == "__main__":
    main()
