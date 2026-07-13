from src.common.http.base_client import BaseClient
from src.common.config.config import Env


class ExperienceClient(BaseClient):

    def __init__(self):
        super().__init__()

        universe_id = Env.UNIVERSE_ID
        self.base_endpoint = self.base_endpoint + f"/universes/{universe_id}"
