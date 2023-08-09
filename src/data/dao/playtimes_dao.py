from requests import HTTPError, get

from src.config.config import Env
from src.data.dao.experience_dao import ExperienceDao


class PlaytimesDao(ExperienceDao):

    def __init__(self):
        super().__init__()

        self.playtimes_endpoint = f"{self.base_endpoint}/ordered-data-stores/{Env.PLAYTIMES_DATASTORE_NAME}/scopes/global/entries"

    def getTop(self, limit: int = 100) -> list[tuple[str, int]]:
        response = get(
            url=self.playtimes_endpoint,
            headers=self.headers,
            params={"orderBy": "value desc", "maxPageSize": limit},
        )

        try:
            response.raise_for_status()
        except HTTPError as e:
            return []
        else:
            entries = response.json()["orderedDataStoreEntries"]
            return [(entry["id"], entry["value"]) for entry in entries]

    def get(self, username: str) -> int | None:
        endpoint = self.playtimes_endpoint + "/" + username
        response = get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except (
            HTTPError
        ) as _:  # no logging because it returns 404 for non-existent player
            return None
        else:
            entry = response.json()
            return entry["value"]
