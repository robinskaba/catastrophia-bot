import json
import os
from dotenv import load_dotenv

ENV_FILE_PATH = ".env"
CONFIG_FILE_PATH = "config.json"

load_dotenv(ENV_FILE_PATH)

_json_data = {}
if os.path.exists(CONFIG_FILE_PATH):
    with open(CONFIG_FILE_PATH, "r") as f:
        _json_data = json.load(f)


def _require_env(key: str) -> str:
    val = os.getenv(key)
    if val is None:
        raise KeyError(f"Missing required ENV variable: {key}")
    return val


def _require_config(key: str):
    val = _json_data.get(key)
    if val is None:
        raise KeyError(f"Missing required Config key: {key}")
    return val


class Env:
    BOT_TOKEN = _require_env("BOT_TOKEN")
    APPLICATION_ID = _require_env("APPLICATION_ID")
    GUILD_ID = _require_env("GUILD_ID")

    API_KEY = _require_env("API_KEY")
    UNIVERSE_ID = _require_env("UNIVERSE_ID")

    PLAYTIMES_DATASTORE_NAME = _require_env("PLAYTIMES_DATASTORE_NAME")
    LEADERBOARDS_DATASTORE_NAME = _require_env("LEADERBOARDS_DATASTORE_NAME")
    LEADERBOARDS_TOP10_DATASTORE_NAME = _require_env(
        "LEADERBOARDS_TOP10_DATASTORE_NAME"
    )
    SPENDERS_DATASTORE_NAME = _require_env("SPENDERS_DATASTORE_NAME")


class Config:
    CONFIDENTIAL_USERNAMES = _require_config("CONFIDENTIAL_USERNAMES")

    TOP_PLAYERS_CHANNEL_ID = int(_require_config("TOP_PLAYERS_CHANNEL_ID"))
    YOUTUBE_VIDEOS_CHANNEL_ID = int(_require_config("YOUTUBE_VIDEOS_CHANNEL_ID"))
    PLAYING_CHANNEL_ID = int(_require_config("PLAYING_CHANNEL_ID"))
    VISITS_CHANNEL_ID = int(_require_config("VISITS_CHANNEL_ID"))
    OWNER_ROLE_ID = int(_require_config("OWNER_ROLE_ID"))

    TICKET_BOT_ID = int(_require_config("TICKET_BOT_ID"))

    NO_MEDIA_CHANNELS = _require_config("NO_MEDIA_CHANNELS")
