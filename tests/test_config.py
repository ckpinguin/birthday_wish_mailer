"""Config loading: OWNER_RECIPIENT handling and required-key checks."""

import json

import pytest

from config import ConfigError, load_config

VALID_DATA = {
    "MAILHOST": "mail.example.com",
    "PORT": "587",
    "LOGIN": "login",
    "PASSWORD": "secret",
    "FROM_ADDR": "from@example.com",
    "SENDER": "Chris",
}


def write_config(tmp_path, data):
    path = tmp_path / "secret.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_owner_recipient_present(tmp_path):
    data = VALID_DATA | {"OWNER_RECIPIENT": "owner@example.com"}
    config = load_config(write_config(tmp_path, data))
    assert config.owner_recipient == "owner@example.com"


def test_owner_recipient_absent_is_none(tmp_path):
    config = load_config(write_config(tmp_path, VALID_DATA))
    assert config.owner_recipient is None


def test_missing_required_key_still_rejected(tmp_path):
    data = dict(VALID_DATA)
    del data["PASSWORD"]
    data["OWNER_RECIPIENT"] = "owner@example.com"
    with pytest.raises(ConfigError, match="PASSWORD"):
        load_config(write_config(tmp_path, data))


def test_stale_spotify_keys_are_ignored(tmp_path):
    data = VALID_DATA | {
        "SPOTIFY_CLIENT_ID": "leftover-id",
        "SPOTIFY_CLIENT_SECRET": "leftover-secret",
    }
    config = load_config(write_config(tmp_path, data))
    assert not hasattr(config, "spotify_client_id")
    assert not hasattr(config, "spotify_client_secret")
