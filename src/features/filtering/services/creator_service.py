import time

from src.features.filtering.daos.creator_dao import CreatorDao
from src.features.filtering.model.creator import Creator


class CreatorService:

    def __init__(self):
        self._creator_dao = CreatorDao()

    def get_or_create(self, discord_id: int) -> Creator:
        creator = self._creator_dao.get(discord_id)
        return creator if creator else self._creator_dao.create(discord_id, time.time())
