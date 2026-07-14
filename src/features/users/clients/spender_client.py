import requests
from src.common.config.config import Config
from src.features.users.clients.experience_client import ExperienceClient


class SpenderClient(ExperienceClient):

    def __init__(self):
        super().__init__()

        self._spender_endpoint = f"{self.base_endpoint}/ordered-data-stores/{Config.SPENDERS_DATASTORE_NAME}/scopes/global/entries"

    def get_roblox_spent(self, username: str) -> int:
        endpoint = self._spender_endpoint + "/" + username
        response = requests.get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return 0

        return response.json().get("value", 0)
