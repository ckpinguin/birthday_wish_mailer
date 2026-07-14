"""Choose templates/images and compose the HTML email body."""

import html
import random
from pathlib import Path

from charts import ChartEntry

TEMPLATE_COUNT = 3
IMAGE_COUNT = 3
TEMPLATE_DIR = Path("letter_templates")
IMAGE_DIR = Path("images")


def choose_template_path() -> Path:
    number = random.randint(1, TEMPLATE_COUNT)
    return TEMPLATE_DIR / f"letter_{number}.txt"


def choose_image_path() -> Path:
    number = random.randint(1, IMAGE_COUNT)
    return IMAGE_DIR / f"small_bday{number}.png"


def fill_placeholders(text: str, firstname: str, gender: str,
                      sender: str) -> str:
    title = "Liebe" if gender == "f" else "Lieber"
    return (text.replace("[TITLE]", title)
            .replace("[NAME]", firstname)
            .replace("[SENDER]", sender))


def render_postscript(birthday: str, entries: list[ChartEntry]) -> str:
    """The 'top songs on your birthday' block; empty if no entries."""
    if not entries:
        return ""
    items = []
    for entry in entries:
        label = html.escape(
            f"Song: {entry.title}, Interpret: {entry.artist}")
        if entry.spotify_url:
            items.append(
                f'<li><a href="{entry.spotify_url}">{label}</a></li>')
        else:
            items.append(f"<li>{label}</li>")
    hint = ("(Falls du kein Spotify hast, kannst du die Songs sehr "
            "leicht auf www.youtube.com finden)")
    return (
        f"<p>P.S. Die 3 Top-Songs der US-Charts am {birthday} waren:"
        f"<br>{hint}</p>"
        f"<ul>{''.join(items)}</ul>"
    )


def compose_html(greeting: str, postscript: str, image_cid: str) -> str:
    greeting_html = html.escape(greeting).replace("\n", "<br>")
    return (
        '<html><head><meta charset="utf-8"></head><body>'
        f"<p>{greeting_html}</p>"
        f"{postscript}"
        f'<p><img src="cid:{image_cid}"></p>'
        "</body></html>"
    )
