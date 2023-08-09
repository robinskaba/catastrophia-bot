import requests
from src.config.config import Env
from src.data.dao.experience_dao import ExperienceDao


class LeaderboardsDao(ExperienceDao):

    def __init__(self):
        super().__init__()

        self.individual_leaderboard_endpoint = f"{self.base_endpoint}/data-stores/{Env.LEADERBOARDS_DATASTORE_NAME}/entries"
        self.leaderboards_top10_endpoint = f"{self.base_endpoint}/data-stores/{Env.LEADERBOARDS_TOP10_DATASTORE_NAME}/entries"

    def get_leaderboard_for_player(self, user_id: str) -> list[tuple[str, str]] | None:
        endpoint = f"{self.individual_leaderboard_endpoint}/{user_id}"
        response = requests.get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return None

        content = response.json()["value"]
        if len(content) == 0:
            return None
        leaderboard_entries = [(name, count) for name, count in content.items()]
        return leaderboard_entries

    def get_leaderboards_top_10(self) -> dict[str : list[tuple[str, str]]] | None:
        endpoint = (
            self.leaderboards_top10_endpoint + "/" + "Top10"
        )  # Top10 is the key to the Top10 record
        response = requests.get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return None

        content = response.json()

        leaderboards = {}
        for leaderboard_name, rankings in content["value"].items():
            leaderboards[leaderboard_name] = [
                (ranking["UserId"], ranking["Count"]) for ranking in rankings
            ]

        return leaderboards
