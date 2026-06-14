import json
from __future__ import annotations
import time

CREATOR_DATA_FILE_PATH = "creators.json"

try:
    with open(CREATOR_DATA_FILE_PATH, "r") as read:
        creator_data = json.load(read)
except FileNotFoundError:
    with open(CREATOR_DATA_FILE_PATH, "w") as write:
        json.dump({}, write, indent=4)


class Creator:

    def __init__(self, discord_id: int, since: float):
        self.discord_id = discord_id
        self.since = since

    @staticmethod
    def get(discord_id: int) -> Creator | None:
        record = creator_data.get(str(discord_id))
        if not record:
            return None
        return Creator(discord_id=discord_id, since=record["since"])

    def save(self):
        creator_data[str(self.discord_id)] = {"since": self.since}

    @staticmethod
    def getOrCreate(discord_id: int) -> Creator:
        creator = Creator.get(discord_id)
        if not creator:
            creator = Creator(discord_id=discord_id, since=time.time())
        return creator
