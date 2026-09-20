import aiohttp
from src.common.config.config import Config
from src.features.users.clients.experience_client import ExperienceClient


class SpenderClient(ExperienceClient):

    def __init__(self):
        super().__init__()

        self._spender_endpoint = f"{self.base_endpoint}/ordered-data-stores/{Config.SPENDERS_DATASTORE_NAME}/scopes/global/entries"

    async def get_roblox_spent(self, username: str) -> int:
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
