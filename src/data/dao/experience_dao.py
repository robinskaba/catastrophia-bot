from src.data.dao.base_dao import BaseDao
from src.config.config import Env


class ExperienceDao(BaseDao):

    def __init__(self):
        super().__init__()

        universe_id = Env.UNIVERSE_ID
        self.base_endpoint = self.base_endpoint + f"/universes/{universe_id}"
