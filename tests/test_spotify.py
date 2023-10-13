import sys
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from jukelify.spotify import SpotifyClient

TESTCASE_ROOT = Path(__file__).parent / "data"


def test_query_item_to_track():
    res = []
    with (TESTCASE_ROOT / "tracks.json").open("r") as filep:
        data = json.load(filep)

    for item in data["tracks"]["items"]:
        res.append(SpotifyClient.query_item_to_track(item))

    assert len(res) == 10


def test_query_item_to_artist():
    res = []
    with (TESTCASE_ROOT / "artist.json").open("r") as filep:
        data = json.load(filep)

    for item in data["artists"]["items"]:
        res.append(SpotifyClient.query_item_to_artist(item))

    assert len(res) == 10


def test_query_item_to_album():
    res = []
    with (TESTCASE_ROOT / "album.json").open("r") as filep:
        data = json.load(filep)

    for item in data["items"]:
        res.append(SpotifyClient.query_item_to_album(item))

    assert len(res) == 1
