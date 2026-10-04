import logging

import aiohttp
from src.common.config.config import Config
from src.features.users.clients.experience_client import ExperienceClient

_logger = logging.getLogger(__name__)


class SpenderClient(ExperienceClient):

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

        self._spender_endpoint = f"{self.base_endpoint}/ordered-data-stores/{Config.SPENDERS_DATASTORE_NAME}/scopes/global/entries"

    async def get_robux_spent(self, username: str) -> int:
        endpoint = self._spender_endpoint + "/" + username

        try:
            async with self._session.get(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return 0

        return data.get("value", 0)

    async def set_robux_spent(self, username: str, amount: int) -> bool:
        endpoint = f"{self._spender_endpoint}/{username}"
        params = {"allowMissing": "true"}
        payload = {"value": amount}
        try:
            async with self._session.patch(
                url=endpoint, headers=self.headers, params=params, json=payload
            ) as response:
                response.raise_for_status()
        except aiohttp.ClientError as e:
            _logger.error(f"failed to set robux spent for {username}: {e}")
            return False
        return True
