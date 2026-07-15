"""Send the composed greeting via SMTP (STARTTLS)."""

import smtplib
from email.message import EmailMessage
from pathlib import Path

from config import AppConfig

IMAGE_CID = "birthday-image"


def build_message(config: AppConfig, to_addr: str, subject: str,
                  html_body: str, image_path: str | Path) -> EmailMessage:
    """HTML mail with the birthday image embedded inline (CID)."""
    message = EmailMessage()
    message["From"] = config.from_addr
    message["To"] = to_addr
    if config.bcc_addr:
        message["Bcc"] = config.bcc_addr
    message["Subject"] = subject
    message.add_alternative(html_body, subtype="html")
    html_part = message.get_payload()[0]
    html_part.add_related(Path(image_path).read_bytes(),
                          maintype="image", subtype="png",
                          cid=f"<{IMAGE_CID}>")
    return message


def send_greeting(config: AppConfig, to_addr: str, subject: str,
                  html_body: str, image_path: str | Path) -> None:
    message = build_message(config, to_addr, subject, html_body, image_path)
    with smtplib.SMTP(config.mailhost, config.port) as connection:
        connection.starttls()
        connection.login(config.login, config.password)
        connection.send_message(message)
