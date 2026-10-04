import logging

import aiohttp
from src.common.config.config import Env
from src.common.db import models
from src.common.http.base_client import BaseClient

_logger = logging.getLogger(__name__)


class GameClient(BaseClient):

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

        self._games_endpoint = "https://games.roblox.com/v1/games"

    async def get_game_stats(self) -> tuple[int, int] | None:
        endpoint = f"{self._games_endpoint}?universeIds={Env.UNIVERSE_ID}&fields=visits%2Cplaying"
        try:
            async with self._session.get(url=endpoint) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as e:
            _logger.error(f"problem fetching game stats: {e}")
            return None

        game_stats = data["data"][0]
        playing, visits = game_stats["playing"], game_stats["visits"]
        return playing, visits
