from src.data.dao.game_dao import GameDao
from src.data.model.game_stats import GameStats
from src.data.dao.leaderboards_dao import LeaderboardsDao
from src.data.dao.playtimes_dao import PlaytimesDao
from src.data.dao.user_dao import UserDao


class StatsService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.playtimes_dao = PlaytimesDao()
        self.leaderboards_dao = LeaderboardsDao()
        self.user_dao = UserDao()
        self.game_dao = GameDao()

    def get_player_playtime(self, username: str) -> int:
        playtime = self.playtimes_dao.get(username)

        # if the username was a bit incorrect it will try to match a user to the username
        if not playtime:
            user = self.user_dao.get_user_from_username(username)
            playtime = self.playtimes_dao.get(user.name) if user else None

        return playtime if playtime else 0

    def get_player_stats(self, user_id: str) -> dict:
        leaderboards_stats = self.leaderboards_dao.get_leaderboard_for_player(user_id)
        leaderboards_stats = leaderboards_stats if leaderboards_stats else []

        stats = {}

        for entry in leaderboards_stats:
            leaderboard_name, value = entry
            stats[leaderboard_name] = value

        return stats

    def get_top_playtimes(self) -> list[tuple]:
        top_times_data = self.playtimes_dao.getTop()
        if not top_times_data:
            return []

        top_times = []
        for entry in top_times_data:
            user_id, playtime = entry
            top_times.append((user_id, playtime))

        return top_times

    def get_top_leaderboard(self, leaderboard_key: str) -> list[dict]:
        all_top10 = self.leaderboards_dao.get_leaderboards_top_10()
        if not all_top10:
            return {}

        leaderboard_top10 = all_top10[leaderboard_key]

        results = []
        cached_usernames = {}
        for entry in leaderboard_top10:
            user_id, value = entry
            username = cached_usernames.get(user_id)
            if not username:
                user = self.user_dao.get_roblox_user(user_id)
                username = user.name if user else "MISSING"
                cached_usernames[user_id] = username

            results.append({username: value})

        return results

    def get_game_stats(self) -> GameStats | None:
        return self.game_dao.get_game_stats()
