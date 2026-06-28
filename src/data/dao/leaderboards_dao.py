from argparse import ArgumentError
from enum import Enum
from datetime import date
import requests
from src.config.config import Config
from src.data.dao.experience_dao import ExperienceDao


class LeaderboardsDao(ExperienceDao):

    def __init__(self):
        super().__init__()

        self.individual_leaderboard_endpoint = f"{self.base_endpoint}/data-stores/{Config.LEADERBOARDS_DATASTORE_NAME}/entries"
        self.leaderboards_top10_endpoint = f"{self.base_endpoint}/data-stores/{Config.LEADERBOARDS_TOP10_DATASTORE_NAME}/entries"

    def get_player_stats(self, user_id: str) -> list[tuple[str, str]] | None:
        endpoint = f"{self.individual_leaderboard_endpoint}/{user_id}"
        response = requests.get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return None

        return response.json()["value"]

    def get_live_leaderboards_top10(self) -> dict[str : list[tuple[str, str]]] | None:
        endpoint = (
            self.leaderboards_top10_endpoint + "/" + Config.LEADERBOARDS_TOP10_KEY
        )
        response = requests.get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return None

        return response.json()["value"]

    def get_past_leaderboards_top10(
        self, month: int | None = None, year: int | None = None
    ):
        if not month and not year:
            raise ArgumentError(
                "Month or year must be set to get past top 10 leaderboard."
            )

        key = "Top10_"
        if month:
            key += f"Monthly_{month:02d}_{year}"
        else:
            key += f"Yearly_{year}"

        endpoint = self.leaderboards_top10_endpoint + "/" + key
        response = requests.get(url=endpoint, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return None
        return response.json()["value"]


class LeaderboardCategory(Enum):
    ALL_TIME = "AllTime"
    YEARLY = "Yearly"
    MONTHLY = "Monthly"
