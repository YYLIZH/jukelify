import json
import random
import re
import textwrap
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, List, Tuple, Union

from requests.exceptions import ReadTimeout
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from jukelify.utils import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


@dataclass
class Track:
    name: str
    uri: str
    artists: str
    img: str
    release_date: str
    album: str
    duration_ms: int

    def __post_init__(self):
        self.name = str(self.name)
        self.album = str(self.album)
        if len(self.album) > 10:
            self.album = self.album[:9] + "..."

    @property
    def duration(self) -> str:
        second = int(self.duration_ms / 1000)
        mins = second // 60
        second = second % 60

        return f"{mins}:{second}"


@dataclass
class Artist:
    name: str
    id: str
    genres: str
    followers: int
    img: str
    uri: str


@dataclass
class Album:
    name: str
    id: str
    img: str
    album_type: str
    uri: str
    release_date: str


def error_handler(func: Callable):
    def wrapper(*args, **kwargs) -> str:
        try:
            result = func(*args, **kwargs)
        except ReadTimeout:
            result = "Timeout Error. Please try again."
        except Exception:
            result = "Unexpected Error."

        return result

    return wrapper


class SpotifyClient:
    scope = ["user-read-playback-state", "user-modify-playback-state"]

    def __init__(self) -> None:
        self.client = Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                scope=self.scope,
                cache_path="spotify.cache",
            )
        )

    def query(self, string: str) -> List[Track]:
        tracks = self.client.search(q=string, type="track")
        result: List[Track] = []

        for item in tracks["tracks"]["items"]:
            result.append(self.query_item_to_track(item))

        return result

    @staticmethod
    def query_item_to_track(item: dict) -> Track:
        """Convert query item to Track object."""
        artists = ", ".join([artist["name"] for artist in item["artists"]])
        try:
            img = item["album"]["images"][0]["url"]
        except (IndexError, KeyError):
            img = ""
        return Track(
            name=item["name"],
            uri=item["uri"],
            artists=artists,
            img=img,
            album=item["album"]["name"],
            release_date=item["album"]["release_date"],
            duration_ms=item["duration_ms"],
        )

    @staticmethod
    def query_item_to_artist(item: dict) -> Artist:
        """Convert query item to Artist object."""
        try:
            img = item["images"][0]["url"]
        except (IndexError, KeyError):
            img = ""
        genres = ", ".join(item["genres"])
        return Artist(
            name=item["name"],
            id=item["id"],
            genres=genres,
            followers=item["followers"]["total"],
            img=img,
            uri=item["uri"],
        )

    @staticmethod
    def query_item_to_album(item: dict) -> Album:
        """Convert query item to Album object."""
        img = item["images"][0]["url"]
        return Album(
            name=item["name"],
            id=item["id"],
            img=img,
            album_type=item["album_type"],
            uri=item["uri"],
            release_date=item["release_date"],
        )

    def add_to_queue(self, track_name: str, track_uri: str) -> Tuple[bool, str]:
        try:
            self.client.add_to_queue(uri=track_uri)
            return True, f"Add {track_name} to your play queue."
        except SpotifyException as error:
            if error.reason == "NO_ACTIVE_DEVICE":
                return (
                    False,
                    "NO_ACTIVE_DEVICE. Please open your spotify and randomly play a song.",
                )
            return False, "Unexpected error."

    @error_handler
    def exec(self, string: str) -> Union[str, dict]:
        print(string)
        if re.match(r"@Jukelify +help *", string):
            return self.display_help()
        if re.match(r"@Jukelify +test *", string):
            return self.quick_test()
        mrx = re.search(r"@Jukelify +(search|random) +(.*)", string)
        if mrx:
            if mrx.group(1) == "search":
                return self.search(mrx.group(2))
            return self.random_push(mrx.group(2))
        return "Sorry. Jukelify cannot parse the instruction."

    def display_help(self) -> str:
        message = """
        Welcome to Jukelify. Jukelify is a service to help you order songs for you or your friends.
        You may use "@Jukelify test" to check if this works properly.

        Subcommands
            search Search results from spotify and return an interactive page.
            random Randomly add a song from the artist
            test   Quick test

        @Jukelify search <song or artist>
        Example:
            @Jukelify search Michael Jackson
            @Jukelify search Butter-Fly

        @Jukelify random <artist>
        Example:
            @Jukelify random 伍佰

        """
        return textwrap.dedent(message).lstrip()

    def quick_test(self) -> str:
        """Perform quick test"""
        query_result = self.query("Never gonna give you up")
        rick_roll = query_result[0]
        succeed, message = self.add_to_queue(rick_roll.name, rick_roll.uri)
        if succeed:
            return "Rick roll! " + message
        return message

    def search(self, string: str) -> dict:
        tracks = self.query(string)
        return create_flex_message_content(tracks)

    def random_push(self, string: str) -> Union[dict, str]:
        artist_result = self.client.search(q=string, limit=1, type="artist")
        artist: Artist = self.query_item_to_artist(artist_result["artists"]["items"][0])

        artist_albums_result = self.client.artist_albums(
            artist_id=artist.id, album_type="album,single", limit=30
        )
        artist_albums = [
            self.query_item_to_album(item) for item in artist_albums_result["items"]
        ]

        tracks_list: List[Track] = []
        # BFS
        while artist_albums:
            album: Album = artist_albums.pop()
            album_tracks_result = self.client.album_tracks(album_id=album.id)
            for item in album_tracks_result["items"]:
                # Pass album info to item
                item["album"] = {
                    "name": album.name,
                    "images": [{"url": album.img}],
                    "release_date": album.release_date,
                }
                tracks_list.append(self.query_item_to_track(item))

        random_num = random.randint(0, len(tracks_list) - 1)
        random_track = tracks_list[random_num]
        succeed, message = self.add_to_queue(
            track_name=random_track.name, track_uri=random_track.uri
        )
        if succeed:
            return create_flex_message_random(random_track)
        return message


Flex_MESSAGE_TEMPLATE = {
    "type": "bubble",
    "size": "giga",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "image",
                "url": "https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/"
                "Spotify_Logo_CMYK_Black.png",
                "size": "xs",
                "align": "center",
                "flex": 0,
                "margin": "none",
                "aspectRatio": "4:3",
            }
        ],
        "paddingAll": "10px",
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [],
        "flex": 0,
        "spacing": "xl",
        "backgroundColor": "#191414",
    },
    "footer": {
        "type": "box",
        "layout": "vertical",
        "contents": [{"type": "text", "text": "Powered by Line and Spotify"}],
    },
    "styles": {"header": {"backgroundColor": "#1DB954"}},
}


def create_search_content(track: Track) -> dict:
    """Create a row of search content in flex message from Track object."""
    template = {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "image",
                        "url": track.img,
                        "aspectRatio": "1:1",
                    }
                ],
                "flex": 0,
                "cornerRadius": "5px",
                "width": "30%",
                "spacing": "none",
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": track.name,
                        "size": "md",
                        "style": "normal",
                        "weight": "bold",
                        "color": "#1DB954",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": track.artists,
                        "size": "xs",
                        "wrap": True,
                        "color": "#FFFFFF",
                    },
                    {
                        "type": "text",
                        "text": track.album,
                        "size": "xs",
                        "wrap": True,
                        "color": "#FFFFFF",
                    },
                    {
                        "type": "text",
                        "text": track.release_date,
                        "size": "xs",
                        "wrap": True,
                        "color": "#FFFFFF",
                    },
                ],
                "spacing": "none",
                "width": "40%",
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "Push",
                            "data": json.dumps({"name": track.name, "uri": track.uri}),
                        },
                        "style": "primary",
                        "color": "#1DB954",
                    }
                ],
                "width": "20%",
            },
        ],
        "spacing": "md",
        "cornerRadius": "5px",
        "backgroundColor": "#191414",
    }
    return template


def create_flex_message_content(tracks: List[Track]) -> dict:
    template = deepcopy(Flex_MESSAGE_TEMPLATE)

    for track in tracks:
        template["body"]["contents"].append(create_search_content(track))

    return template


def create_flex_message_random(track: Track) -> dict:
    template = deepcopy(Flex_MESSAGE_TEMPLATE)

    template["body"]["contents"] = [
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "Randomly pick a song for you. Hope you will like it!",
                    "color": "#FFFFFF",
                }
            ],
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "image",
                            "url": track.img,
                            "aspectRatio": "1:1",
                        }
                    ],
                    "flex": 0,
                    "cornerRadius": "5px",
                    "width": "40%",
                    "spacing": "none",
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": track.name,
                            "size": "lg",
                            "style": "normal",
                            "weight": "bold",
                            "color": "#1DB954",
                            "wrap": True,
                        },
                        {
                            "type": "text",
                            "text": track.duration,
                            "wrap": True,
                            "color": "#FFFFFF",
                        },
                        {
                            "type": "text",
                            "text": track.album,
                            "color": "#FFFFFF",
                        },
                        {
                            "type": "text",
                            "text": track.release_date,
                            "color": "#FFFFFF",
                        },
                    ],
                    "spacing": "none",
                    "width": "40%",
                },
            ],
            "spacing": "lg",
            "cornerRadius": "5px",
            "backgroundColor": "#191414",
        },
    ]
    return template


spotify_api = SpotifyClient()
