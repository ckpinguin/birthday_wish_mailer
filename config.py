"""Load and validate the application configuration (.secret.json)."""

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILE = ".secret.json"

REQUIRED_KEYS = (
    "MAILHOST",
    "PORT",
    "LOGIN",
    "PASSWORD",
    "FROM_ADDR",
    "SENDER",
)


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    mailhost: str
    port: int
    login: str
    password: str
    from_addr: str
    sender: str
    bcc_addr: str | None = None
    test_recipient: str | None = None
    owner_recipient: str | None = None


def load_config(path: str | Path = CONFIG_FILE) -> AppConfig:
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"config file is not valid JSON: {path}") from exc

    missing = [key for key in REQUIRED_KEYS if not data.get(key)]
    if missing:
        raise ConfigError(
            f"config file {path} is missing keys: {', '.join(missing)}")

    try:
        port = int(data["PORT"])
    except (TypeError, ValueError) as exc:
        raise ConfigError(
            f"PORT must be a number, got: {data['PORT']!r}") from exc

    return AppConfig(
        mailhost=data["MAILHOST"],
        port=port,
        login=data["LOGIN"],
        password=data["PASSWORD"],
        from_addr=data["FROM_ADDR"],
        sender=data["SENDER"],
        bcc_addr=data.get("BCC_ADDR"),
        test_recipient=data.get("TEST_RECIPIENT"),
        owner_recipient=data.get("OWNER_RECIPIENT"),
    )
