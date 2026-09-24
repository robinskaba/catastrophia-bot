from datetime import UTC, datetime

import aiohttp
import asyncpg
from src.common.db.command_usage import get_searched_stats_usernames_by_discord_id
from src.features.stats.clients.game_client import GameClient
from src.features.stats.clients.leaderboards_client import LeaderboardsClient
from src.features.stats.clients.playtimes_client import PlaytimesClient
from src.features.stats.model.game_stats import GameStats
from src.features.users.clients.user_client import UserClient
from src.features.users.services.user_service import UserService


class StatsService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

        self._playtimes_client = PlaytimesClient()
        self._leaderboard_client = LeaderboardsClient()
        self._user_client = UserClient()
        self._game_client = GameClient()

        self._user_service = None

    def set_services(self, user_service: UserService):
        self._user_service = user_service

    def set_session(self, session: aiohttp.ClientSession):
        self._playtimes_client.set_session(session)
        self._leaderboard_client.set_session(session)
        self._user_client.set_session(session)
        self._game_client.set_session(session)

    def set_pool(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_player_playtime(self, username: str) -> int:
        playtime = await self._playtimes_client.get(username)
        return playtime if playtime else 0

    async def get_player_stats(
        self, user_id: str, month: int | None, year: int | None
    ) -> dict | None:
        player_stats = await self._leaderboard_client.get_player_stats(user_id)
        if not player_stats:
            return None
        if not month and not year:
            return player_stats["AllTime"]
        if month:
            return player_stats["Monthly"].get(f"{month:02d}_{year}")
        return player_stats["Yearly"].get(f"{year}")

    async def get_top_playtimes(self) -> list[tuple]:
        top_times_data = await self._playtimes_client.getTop()
        if not top_times_data:
            return []

        top_times = []
        for entry in top_times_data:
            user_id, playtime = entry
            top_times.append((user_id, playtime))

        return top_times

    async def get_top_leaderboard(
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
            live_record = await self._leaderboard_client.get_live_leaderboards_top10()
            if not live_record:
                return None
            if not month and not year:
                leaderboards = live_record["AllTime"]
            elif not month and year:
                leaderboards = live_record["Yearly"]
            else:
                leaderboards = live_record["Monthly"]
        else:
            leaderboards = await self._leaderboard_client.get_past_leaderboards_top10(
                month=month, year=year
            )
            if not leaderboards:
                return None

        leaderboard = leaderboards[leaderboard_key]
        results = []
        for entry in leaderboard:
            user_id, value = entry["UserId"], entry["Count"]
            username = await self._user_service.get_username(user_id)
            results.append((username if username else "???", value))

        return results

    async def get_game_stats(self) -> GameStats | None:
        return await self._game_client.get_game_stats()

    async def get_predicted_usernames_from_searches(
        self, discord_id: int
    ) -> list[tuple[str, float]] | None:
        async with self._pool.acquire() as conn:
            searches = await get_searched_stats_usernames_by_discord_id(
                conn=conn, discord_id=discord_id, limit=3
            )
        if len(searches) < 1:
            return None
        total = sum(x.search_count for x in searches)
        searches.sort(key=lambda a: a.search_count, reverse=True)
        return [(x.username, x.search_count / total * 100) for x in searches]
