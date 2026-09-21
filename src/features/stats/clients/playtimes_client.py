import aiohttp

from src.common.config.config import Config
from src.features.users.clients.experience_client import ExperienceClient


class PlaytimesClient(ExperienceClient):

    def __init__(self):
        super().__init__()

        self._playtimes_endpoint = f"{self.base_endpoint}/ordered-data-stores/{Config.PLAYTIMES_DATASTORE_NAME}/scopes/global/entries"

    async def getTop(self, limit: int = 100) -> list[tuple[str, int]]:
        try:
            async with self._session.get(
                url=self._playtimes_endpoint,
                headers=self.headers,
                params={"orderBy": "value desc", "maxPageSize": limit},
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return []
        else:
            entries = data["orderedDataStoreEntries"]
            return [(entry["id"], entry["value"]) for entry in entries]

    async def get(self, username: str) -> int | None:
        endpoint = self._playtimes_endpoint + "/" + username

        try:
            async with self._session.get(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except (
            aiohttp.ClientError
        ) as _:  # no logging because it returns 404 for non-existent player
            return None
        else:
            return data["value"]
