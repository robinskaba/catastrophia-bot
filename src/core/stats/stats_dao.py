from src.data.database.database import Database


class StatsDao:

    def __init__(self):
        self._db = Database()

    def save_stats_search(self, discord_id: int, rbx_username: str):
        self._db.cursor.execute(
            "INSERT INTO stats_searches (discord_id, rbx_username) VALUES (?, ?)",
            (discord_id, rbx_username),
        )
        self._db.conn.commit()

    def get_search_counts_by_discord_id_for_username(
        self, discord_id: int
    ) -> list[tuple[str, int]]:
        self._db.cursor.execute(
            "SELECT rbx_username, COUNT(*) FROM stats_searches WHERE discord_id = ? GROUP BY rbx_username",
            (discord_id,),
        )
        result = self._db.cursor.fetchall()
        return result
