from argparse import ArgumentError
import logging
import aiohttp
from src.common.config.config import Config, Env
from src.features.users.clients.experience_client import ExperienceClient

_logger = logging.getLogger(__name__)


class LeaderboardsClient(ExperienceClient):

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

        self._individual_leaderboard_endpoint = f"{self.base_endpoint}/data-stores/{Config.LEADERBOARDS_DATASTORE_NAME}/entries"
        self._leaderboards_top10_endpoint = f"{self.base_endpoint}/data-stores/{Config.LEADERBOARDS_TOP10_DATASTORE_NAME}/entries"

    async def get_player_stats(self, user_id: str):
        endpoint = f"{self._individual_leaderboard_endpoint}/{user_id}"

        try:
            async with self._session.get(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return None

        return data["value"]

    async def set_player_stats(self, user_id: int, stats) -> bool:
        # universe-datastores.objects:update
        endpoint = f"https://apis.roblox.com/cloud/v2/universes/{Env.UNIVERSE_ID}/data-stores/{Config.LEADERBOARDS_DATASTORE_NAME}/entries/{user_id}"
        params = {"allowMissing": "true"}
        payload = {"value": stats}
        try:
            async with self._session.patch(
                url=endpoint, headers=self.headers, params=params, json=payload
            ) as response:
                response.raise_for_status()
        except aiohttp.ClientError as e:
            _logger.error(f"failed to set leaderboard stats of player {user_id}: {e}")
            return False
        return True

    async def delete_player_stats(self, user_id: int) -> bool:
        # universe-datastores.objects:delete
        endpoint = f"https://apis.roblox.com/cloud/v2/universes/{Env.UNIVERSE_ID}/data-stores/{Config.LEADERBOARDS_DATASTORE_NAME}/entries/{user_id}"
        try:
            async with self._session.delete(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
        except aiohttp.ClientError as e:
            _logger.error(f"failed to delete stats of player {user_id}: {e}")
            return False
        return True

    async def get_live_leaderboards_top10(
        self,
    ) -> dict[str : list[tuple[str, str]]] | None:
        endpoint = (
            self._leaderboards_top10_endpoint + "/" + Config.LEADERBOARDS_TOP10_KEY
        )

        try:
            async with self._session.get(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return None

        return data["value"]

    async def get_past_leaderboards_top10(
        self, month: int | None = None, year: int | None = None
    ):
        # TODO move validation logic to service
        if not month and not year:
            raise ArgumentError(
                "Month or year must be set to get past top 10 leaderboard."
            )

        key = "Top10_"
        if month:
            key += f"Monthly_{month:02d}_{year}"
        else:
            key += f"Yearly_{year}"

        endpoint = self._leaderboards_top10_endpoint + "/" + key
        try:
            async with self._session.get(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return None
        return data["value"]
