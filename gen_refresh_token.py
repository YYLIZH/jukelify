from spotipy.oauth2 import SpotifyOAuth

from jukelify.utils import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


def generate_access_token():
    scope = ["user-read-playback-state", "user-modify-playback-state"]
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        scope=scope,
        cache_path="spotify.cache",
    )
    auth_manager.get_access_token(as_dict=False)
    print("Generate access token and refresh token at spotify.cache")


if __name__ == "__main__":
    generate_access_token()
