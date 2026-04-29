import logging

import requests
from src.config.config import Env
from src.data.model.game_stats import GameStats

logger = logging.getLogger(__name__)


class GameDao:

    def __init__(self):
        super().__init__()

        self.games_endpoint = "https://games.roblox.com/v1/games"

    def get_game_stats(self) -> GameStats | None:
        endpoint = f"{self.games_endpoint}?universeIds={Env.UNIVERSE_ID}"
        try:
            response = requests.get(url=endpoint)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"problem fetching game stats: {e}")
            return -1

        return GameStats.from_dict(response.json()["data"][0])
