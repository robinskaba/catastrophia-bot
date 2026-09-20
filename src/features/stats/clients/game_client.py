import logging

import aiohttp
from src.common.config.config import Env
from src.common.http.base_client import BaseClient
from src.features.stats.model.game_stats import GameStats

_logger = logging.getLogger(__name__)


class GameClient(BaseClient):

    def __init__(self):
        super().__init__()

        self._games_endpoint = "https://games.roblox.com/v1/games"

    async def get_game_stats(self) -> GameStats | None:
        endpoint = f"{self._games_endpoint}?universeIds={Env.UNIVERSE_ID}&fields=visits%2Cplaying"
        try:
            async with self._session.get(url=endpoint) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as e:
            _logger.error(f"problem fetching game stats: {e}")
            return None
        return GameStats.from_dict(data["data"][0])
