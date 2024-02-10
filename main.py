from email.message import EmailMessage
import smtplib
import json
import pandas
import random
import datetime as dt
import socks
from billboard_timemachine import BillboardTimeMachine
from spotifier import Spotifier


try:
    with open(".secret.json", "r") as config_file:
        config_data: dict = json.load(config_file)
except FileNotFoundError:
    print("ERROR: No config file found!")
    exit(0)


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


BIRTHDAY_FILE = "TEST_birthdays.csv"


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


def send_mail_for_all_bday_persons(
        persons_with_birthday: list[dict],
        top_three_songs_for_birthday: list[tuple],
        spotify_urls: list[str]) -> None:
    for person in persons_with_birthday:
        template_content = read_random_template()
        content = replace_content(
            template_content, person['firstname'], person['gender'])
        content_special = "\n\nP.S. Die 3 Top-Songs der US-Charts an deinem Geburtsdatum waren:\n\n"
        i = 0
        for song, artist in top_three_songs_for_birthday:
            content_special += f"Song: {song}, Interpret: {artist}: {spotify_urls[i]}\n"
            i += 1
        content += "\n" + content_special
        send_mail(person['email'], content, bcc=BCC_ADDR)


# ___ MAIN ____
persons_with_birthday = find_persons_with_birthday_today(BIRTHDAY_FILE)

for person in persons_with_birthday:
    year = str(person['year'])
    month = str(person['month']).zfill(2)
    day = str(person['day']).zfill(2)
    billboard = BillboardTimeMachine(
        f"{year}-{month}-{day}")
    top_three_songs_for_birthday = billboard.get_top_three_artists_and_tracks()
    spotify = Spotifier(*zip(*top_three_songs_for_birthday))
    spotify_urls = spotify.get_spotify_urls()

send_mail_for_all_bday_persons(
    persons_with_birthday, top_three_songs_for_birthday, spotify_urls=spotify_urls)
