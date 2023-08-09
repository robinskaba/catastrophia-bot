import requests
from src.config.config import Env
from src.data.dao.experience_dao import ExperienceDao


class SpenderDao(ExperienceDao):

    def __init__(self):
        super().__init__()

        self.spender_endpoint = f"{self.base_endpoint}/ordered-data-stores/{Env.SPENDERS_DATASTORE_NAME}/scopes/global/entries"

    def get_roblox_spent(self, username: str) -> int:
        endpoint = self.spender_endpoint + "/" + username
        response = requests.get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return 0

        return response.json().get("value", 0)
