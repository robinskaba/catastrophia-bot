import requests
from src.config.config import Env
from src.data.model.game_stats import GameStats


class GameDao:

    def __init__(self):
        super().__init__()

        self.games_endpoint = "https://games.roblox.com/v1/games"

    def get_game_stats(self) -> GameStats | None:
        endpoint = f"{self.games_endpoint}?universeIds={Env.UNIVERSE_ID}"
        response = requests.get(url=endpoint)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(e)
            return -1

        return GameStats.from_dict(response.json()["data"][0])
