import logging

import requests
from src.common.config.config import Env
from src.features.stats.model.game_stats import GameStats

_logger = logging.getLogger(__name__)


class GameClient:

    def __init__(self):
        super().__init__()

        self._games_endpoint = "https://games.roblox.com/v1/games"

    def get_game_stats(self) -> GameStats | None:
        endpoint = f"{self._games_endpoint}?universeIds={Env.UNIVERSE_ID}"
        try:
            response = requests.get(url=endpoint)
            response.raise_for_status()
        except requests.RequestException as e:
            _logger.error(f"problem fetching game stats: {e}")
            return None
        return GameStats.from_dict(response.json()["data"][0])
