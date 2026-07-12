from datetime import UTC, datetime
import logging
from src.core.stats.stats_dao import StatsDao
from src.data.http.game_dao import GameDao
from src.data.http.leaderboards_dao import LeaderboardsDao
from src.data.http.playtimes_dao import PlaytimesDao
from src.data.http.user_dao import UserDao
from src.data.model.game_stats import GameStats

_logger = logging.getLogger(__name__)


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

        self.stats_dao = StatsDao()

    def get_player_playtime(self, username: str) -> int:
        playtime = self.playtimes_dao.get(username)
        return playtime if playtime else 0

    def get_player_stats(
        self, user_id: str, month: int | None, year: int | None
    ) -> dict | None:
        player_stats = self.leaderboards_dao.get_player_stats(user_id)
        if not player_stats:
            return None
        if not month and not year:
            return player_stats["AllTime"]
        if month:
            return player_stats["Monthly"].get(f"{month:02d}_{year}")
        return player_stats["Yearly"].get(f"{year}")

    def get_top_playtimes(self) -> list[tuple]:
        top_times_data = self.playtimes_dao.getTop()
        if not top_times_data:
            return []

        top_times = []
        for entry in top_times_data:
            user_id, playtime = entry
            top_times.append((user_id, playtime))

        return top_times

    def get_top_leaderboard(
        self, leaderboard_key: str, month: int | None = None, year: int | None = None
    ) -> list[tuple] | None:
        leaderboards = {}

        # leaderboards data is in the common record
        current_date = datetime.now(tz=UTC)
        if (not month and not year) or (
            (
                month
                and year
                and month == current_date.month
                and year == current_date.year
            )
            or (not month and year and year == current_date.year)
        ):
            live_record = self.leaderboards_dao.get_live_leaderboards_top10()
            if not live_record:
                return None
            if not month and not year:
                leaderboards = live_record["AllTime"]
            elif not month and year:
                leaderboards = live_record["Yearly"]
            else:
                leaderboards = live_record["Monthly"]
        else:
            leaderboards = self.leaderboards_dao.get_past_leaderboards_top10(
                month=month, year=year
            )
            if not leaderboards:
                return None

        leaderboard = leaderboards[leaderboard_key]
        results = []
        cached_usernames = {}
        for entry in leaderboard:
            user_id, value = entry["UserId"], entry["Count"]
            username = cached_usernames.get(user_id)
            if not username:
                user = self.user_dao.get_roblox_user(user_id)
                username = user.name if user else "MISSING"
                cached_usernames[user_id] = username

            results.append((username, value))

        return results

    def get_game_stats(self) -> GameStats | None:
        return self.game_dao.get_game_stats()

    def save_stat_search(self, discord_id: int, rbx_username: str):
        self.stats_dao.save_stats_search(discord_id, rbx_username)

    def get_predicted_usernames_from_searches(
        self, discord_id: int
    ) -> list[tuple[str, float]] | None:
        searches = self.stats_dao.get_search_counts_by_discord_id_for_username(
            discord_id
        )
        if len(searches) < 1:
            return None

        total = sum(x[1] for x in searches)
        searches.sort(key=lambda a: a[1], reverse=True)
        return [(username, count / total * 100) for username, count in searches]
