import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json


class Spotifier():
    try:
        with open(".secret.json", "r") as config_file:
            config_data = json.load(config_file)
    except FileNotFoundError:
        print("ERROR: No config file found!")
        exit(0)

    SPOTIFY_CLIENT_ID = config_data["SPOTIFY_CLIENT_ID"]
    SPOTIFY_CLIENT_SECRET = config_data["SPOTIFY_CLIENT_SECRET"]

    def __init__(self, tracks: list, artists: list) -> None:
        self.tracks = tracks
        self.artists = artists
        self.spotify = self.__authenticate()

    def __authenticate(self) -> spotipy.Spotify:
        auth_base = spotipy.oauth2.SpotifyOAuth(
            client_id=self.SPOTIFY_CLIENT_ID,
            client_secret=self.SPOTIFY_CLIENT_SECRET,
            redirect_uri="http://example.com", scope="playlist-modify-private")
        auth_base.get_access_token()
        return spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials
            (client_id=self.SPOTIFY_CLIENT_ID,
             client_secret=self.SPOTIFY_CLIENT_SECRET))

    def get_spotify_urls(self) -> list:
        urls = []
        track_ids = []

        for track in self.tracks:
            print(track)
            index = self.tracks.index(track)
            artist = self.artists[index]
            results = self.spotify.search(q=f"{track}%2520{artist}")
            if "tracks" in results and "items" \
                    in results["tracks"] and results["tracks"]["items"]:
                hit = results["tracks"]["items"][0]
                track_id = hit["uri"]
                track_ids.append(track_id)
                spotify_url = hit['external_urls']['spotify']
                urls.append(spotify_url)

            # print(track_ids)
            # print(urls)
        return urls
