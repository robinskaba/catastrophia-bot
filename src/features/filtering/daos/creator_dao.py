from src.common.database.database import Database
from src.features.filtering.model.creator import Creator


class CreatorDao:

    def __init__(self):
        self._db = Database()

    def create(self, discord_id: int, since: float) -> Creator:
        self._db.cursor.execute(
            "INSERT INTO creators (discord_id, since) VALUES (?, ?)",
            (discord_id, since),
        )
        self._db.conn.commit()
        return Creator(discord_id=discord_id, since=since)

    def get(self, discord_id: int) -> Creator:
        self._db.cursor.execute(
            "SELECT discord_id, since FROM creators WHERE discord_id = ?", (discord_id,)
        )
        result = self._db.cursor.fetchone()
        if not result:
            return None
        discord_id, since = result
        return Creator(discord_id=discord_id, since=since)
