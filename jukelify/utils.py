import os
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()


def _assert_necessary(key: str) -> str:
    """Assert key is valid is environment varialble

    Args:
        key (str): The key you want to check in the environment variable.

    Returns:
        value (str): The value of the environment variable

    Raises:
        ValueError: Raise ValueError if user forget to set the key, value pair
            in the .env file.

    """
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"{key} must be set in .env file.")
    return value


def _load_line_config() -> Tuple[str, str]:
    """Load line config."""
    channel_secret = _assert_necessary("LINE_CHANNEL_SECRET")
    channel_access_token = _assert_necessary("LINE_CHANNEL_ACCESS_TOKEN")
    return channel_secret, channel_access_token


def _load_spotify_config() -> Tuple[str]:
    """Load spotify config."""
    client_id = _assert_necessary("SPOTIFY_CLIENT_ID")
    client_secret = _assert_necessary("SPOTIFY_CLIENT_SECRET")
    redirect_uri = _assert_necessary("SPOTIFY_REDIRECT_URI")
    os.environ["SPOTIPY_CLIENT_ID"] = client_id
    os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
    os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri
    return client_id, client_secret


LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN = _load_line_config()
(
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
) = _load_spotify_config()
