import logging

import aiohttp

from src.common.config.config import Config, Env
from src.features.users.clients.experience_client import ExperienceClient

_logger = logging.getLogger(__name__)


class PlaytimesClient(ExperienceClient):

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

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

    async def patch(self, username: str, playtime: int) -> bool:
        # universe.ordered-data-store.scope.entry:write
        endpoint = f"https://apis.roblox.com/cloud/v2/universes/{Env.UNIVERSE_ID}/ordered-data-stores/{Config.PLAYTIMES_DATASTORE_NAME}/scopes/global/entries/{username}"
        params = {
            "allowMissing": "true",
        }
        payload = {"value": playtime}
        try:
            async with self._session.patch(
                url=endpoint, headers=self.headers, params=params, json=payload
            ) as response:
                response.raise_for_status()
        except aiohttp.ClientError as e:
            _logger.error(f"failed to update playtime of {username}: {e}")
            return False
        return True

    async def delete(self, username: str) -> bool:
        endpoint = f"https://apis.roblox.com/cloud/v2/universes/{Env.UNIVERSE_ID}/ordered-data-stores/{Config.PLAYTIMES_DATASTORE_NAME}/scopes/global/entries/{username}"
        try:
            async with self._session.delete(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
        except aiohttp.ClientError as e:
            _logger.error(f"failed to delete playtime of {username}: {e}")
            return False
        return True
