import json
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import aiohttp
import asyncpg

from src.common.config.config import Config
from src.common.db.command_usage import get_searched_stats_usernames_by_discord_id
from src.common.db.game_stats import create_game_stats_record, get_latest_game_stats
from src.common.db.leaderboards_cache import (
    get_leaderboards_cache,
    upsert_leaderboards_cache,
)
from src.common.db.models import GameStat
from src.features.stats.clients.game_client import GameClient
from src.features.stats.clients.leaderboards_client import LeaderboardsClient
from src.features.stats.clients.playtimes_client import PlaytimesClient
from src.features.users.clients.user_client import UserClient
from src.features.users.user_service import UserService

_logger = logging.getLogger(__name__)
_local_tz = ZoneInfo(Config.TIMEZONE)


class StatsService:

    def __init__(
        self,
        session: aiohttp.ClientSession,
        pool: asyncpg.Pool,
        user_service: UserService,
    ):
        self._pool: asyncpg.Pool = pool

        self._playtimes_client = PlaytimesClient(session)
        self._leaderboard_client = LeaderboardsClient(session)
        self._user_client = UserClient(session)
        self._game_client = GameClient(session)

        self._user_service = user_service

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

    async def get_player_stats_graphed(
        self, user_id: str, stat_key: str
    ) -> tuple[list[str], list[int]] | None:
        data = await self._leaderboard_client.get_player_stats(user_id)
        if not data:
            return None

        graph_months, graph_values = [], []

        # extract months data
        monthly_data = data.get("Monthly", {})
        monthly_data.pop(
            "06_2026", None
        )  # when leaderboards released, makes graphs look bad
        months_sorted = sorted(
            monthly_data.keys(), key=lambda x: (x.split("_")[1], x.split("_")[0])
        )
        for month in months_sorted:
            graph_months.append(month)
            graph_values.append(monthly_data.get(month, {}).get(stat_key, 0))
        return graph_months, graph_values

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
            # try retrieving cached data
            async with self._pool.acquire() as conn:
                period = f"{month:02d}_{year}" if month else f"{year}"
                leaderboards_cache = await get_leaderboards_cache(conn, period=period)
                if (
                    not leaderboards_cache
                    or (current_date - leaderboards_cache.refreshed_at).days > 30
                ):
                    # fetch latest data
                    leaderboards = (
                        await self._leaderboard_client.get_past_leaderboards_top10(
                            month=month, year=year
                        )
                    )
                    if not leaderboards:
                        return None  # non-existent period
                    await upsert_leaderboards_cache(
                        conn, period=period, leaderboard_data=json.dumps(leaderboards)
                    )
                else:
                    leaderboards = json.loads(leaderboards_cache.leaderboard_data)

        leaderboard = leaderboards[leaderboard_key]
        results = []
        for entry in leaderboard:
            user_id, value = entry["UserId"], entry["Count"]
            username = await self._user_service.get_username(user_id)
            results.append((username if username else "???", value))

        return results

    async def record_game_stats(self):
        stats = await self._game_client.get_game_stats()
        if not stats:
            _logger.warning("failed to fetch game stats from API")
            return
        async with self._pool.acquire() as conn:
            playing, visits = stats
            await create_game_stats_record(conn, playing=playing, visits=visits)

    async def get_game_stats(self) -> GameStat | None:
        async with self._pool.acquire() as conn:
            return await get_latest_game_stats(conn)

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

    async def transfer_stats(self, source_username: str, target_username: str) -> bool:
        # identification
        source_user = await self._user_service.get_user(source_username)
        target_user = await self._user_service.get_user(target_username)
        if not source_user or not target_user:
            # TODO propagate error
            _logger.error("failed to transfer stats - unknown users")
            return False

        # fetch
        source_playtime = await self._playtimes_client.get(source_username)
        source_stats = await self._leaderboard_client.get_player_stats(source_user.id)
        source_robux = await self._user_service.get_robux_spent(source_user)
        if not source_playtime or not source_stats or not source_robux:
            _logger.error(
                f"failed to transfer stats - missing source data ({source_playtime=}, {source_stats=}, {source_robux=})"
            )
            return False

        # transfer
        playtime_transfer = await self._playtimes_client.patch(
            target_username, source_playtime
        )
        stats_transfer = await self._leaderboard_client.set_player_stats(
            target_user.id, source_stats
        )
        robux_transfer = await self._user_service.set_robux_spent(
            target_user, source_robux
        )
        if not playtime_transfer or not stats_transfer or not robux_transfer:
            _logger.error("failed to transfer stats - problem during migration")
            return False

        # clean up of old data
        clean_playtime = await self._playtimes_client.delete(source_username)
        clean_stats = await self._leaderboard_client.delete_player_stats(source_user.id)
        clean_robux = await self._user_service.set_robux_spent(source_user, 0)
        if not clean_playtime or not clean_stats or not clean_robux:
            _logger.error("failed to transfer stats - problem deleting source data")
            return False

        return True
