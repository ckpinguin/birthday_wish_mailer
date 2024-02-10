from bs4 import BeautifulSoup
import requests


class BillboardTimeMachine:
    # Should be stable enough to be a constant:
    URL_BILLBOARD = "https://www.billboard.com/charts/hot-100/"

    def __init__(self, date: str) -> None:
        self.date_str = date

    def __getBillboard(self) -> str:
        url = f"{self.URL_BILLBOARD}{self.date_str}"
        print(f"getting data on {url}")
        response = requests.get(url)
        if response.status_code != 200:
            raise f"Failed to retrieve the page {url}. Status Code:\
            {response.status_code}"
        return response.text

    def __get_artists_and_tracks(self, html_data: str) -> list:
        tracks = []
        artists = []
        soup = BeautifulSoup(html_data, 'html.parser')

        songs_name = soup.select(selector="li h3.c-title")
        artists_name = soup.select(
            'li.o-chart-results-list__item span.c-label.a-no-trucate')

        for song in songs_name:
            tracks.append(song.get_text(strip=True))
        for artist in artists_name:
            artists.append(artist.get_text(strip=True))

        return list(zip(tracks, artists))

    def get_top_three_artists_and_tracks(self) -> list:
        data = self.__getBillboard()
        result = self.__get_artists_and_tracks(data)
        return result[:3]
