from argparse import ArgumentError
import aiohttp
from src.common.config.config import Config
from src.features.users.clients.experience_client import ExperienceClient


class LeaderboardsClient(ExperienceClient):

    def __init__(self):
        super().__init__()

        self._individual_leaderboard_endpoint = f"{self.base_endpoint}/data-stores/{Config.LEADERBOARDS_DATASTORE_NAME}/entries"
        self._leaderboards_top10_endpoint = f"{self.base_endpoint}/data-stores/{Config.LEADERBOARDS_TOP10_DATASTORE_NAME}/entries"

    async def get_player_stats(self, user_id: str) -> list[tuple[str, str]] | None:
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
