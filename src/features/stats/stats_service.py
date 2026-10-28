import dataclasses
import json
import logging
import math
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp
import asyncpg

from src.common.config.config import Config
from src.common.db.command_usage import get_searched_stats_usernames_by_discord_id
from src.common.db.game_stats import (
    create_game_stats_record,
    get_first_game_stats,
    get_latest_game_stats,
    get_playing_history,
    get_playing_low,
    get_playing_peak,
)
from src.common.db.leaderboards_cache import (
    get_leaderboards_cache,
    upsert_leaderboards_cache,
)
from src.common.db.models import GameStat
from src.common.db.player_stats_cache import (
    get_player_stats_cache,
    upsert_player_stats_cache,
)
from src.features.stats.clients.game_client import GameClient
from src.features.stats.clients.leaderboards_client import LeaderboardsClient
from src.features.stats.clients.playtimes_client import PlaytimesClient
from src.features.users.clients.user_client import UserClient
from src.features.users.user_service import UserService

_logger = logging.getLogger(__name__)
_local_tz = ZoneInfo(Config.TIMEZONE)


_PLAYER_STATS_CACHE_LIFETIME_SECONDS = 15 * 60

# period -> (time span, bucket size in seconds), buckets keep graphs at ~150-250 points
PLAYING_PERIODS: dict[str, tuple[timedelta, int]] = {
    "24h": (timedelta(hours=24), 10 * 60),
    "3d": (timedelta(days=3), 30 * 60),
    "7d": (timedelta(days=7), 60 * 60),
    "30d": (timedelta(days=30), 3 * 60 * 60),
}
PLAYING_ALL_TIME = "all"
_ALL_TIME_TARGET_BUCKETS = 240


@dataclasses.dataclass()
class PlayingHistory:
    times: list[datetime]
    averages: list[float | None]
    lows: list[int | None]
    highs: list[int | None]
    peak: GameStat
    lowest: GameStat


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

    async def _fetch_player_stats(self, user_id: str) -> dict | None:
        async with self._pool.acquire() as conn:
            stats_cache = await get_player_stats_cache(conn, user_id=user_id)
            if (
                not stats_cache
                or (
                    datetime.now(tz=stats_cache.refreshed_at.tzinfo)
                    - stats_cache.refreshed_at
                ).seconds
                > _PLAYER_STATS_CACHE_LIFETIME_SECONDS
            ):
                current_stats = await self._leaderboard_client.get_player_stats(user_id)
                if not current_stats:
                    return None
                await upsert_player_stats_cache(
                    conn, user_id=user_id, stats=json.dumps(current_stats)
                )
                return current_stats
            return json.loads(stats_cache.stats)

    async def get_player_playtime(self, username: str) -> int:
        playtime = await self._playtimes_client.get(username)
        return playtime if playtime else 0

    async def get_player_stats_for_period(
        self, user_id: str, month: int | None, year: int | None
    ) -> dict | None:
        player_stats = await self._fetch_player_stats(user_id)
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
        data = await self._fetch_player_stats(user_id)
        if not data:
            return None

        graph_months, graph_values = [], []

        # extract months data
        monthly_data = data.get("Monthly", {})
        monthly_data.pop(
            "06_2026", None
        )  # when leaderboards released, makes graphs look bad

        current_date = datetime.now(tz=UTC)
        current_year, current_month = current_date.year, current_date.month

        # normalize monthly data to include data from 07_2026 all the way to the current date
        y, m = 2026, 7
        while y < current_year or (y == current_year and m <= current_month):
            month_str = f"{m:02d}_{y}"
            graph_months.append(month_str)
            graph_values.append(monthly_data.get(month_str, {}).get(stat_key, 0))

            m += 1
            if m > 12:
                m = 1
                y += 1

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

        current_date = datetime.now(tz=UTC)
        is_all_time = not month and not year
        is_current_period = (
            month and year and month == current_date.month and year == current_date.year
        ) or (not month and year and year == current_date.year)

        if is_current_period or is_all_time:
            live_record = await self._leaderboard_client.get_live_leaderboards_top10()
            if not live_record:
                return None
            if is_all_time:
                leaderboards = live_record["AllTime"]
            elif not month and year:
                leaderboards = live_record["Yearly"]
            else:
                leaderboards = live_record["Monthly"]
        else:
            async with self._pool.acquire() as conn:
                period = f"{month:02d}_{year}" if month else f"{year}"

                leaderboards_cache = await get_leaderboards_cache(conn, period=period)
                if (
                    not leaderboards_cache
                    or (current_date - leaderboards_cache.refreshed_at).days > 30
                ):
                    leaderboards = (
                        await self._leaderboard_client.get_past_leaderboards_top10(
                            month=month, year=year
                        )
                    )
                    if not leaderboards:
                        return None

                    await upsert_leaderboards_cache(
                        conn, period=period, leaderboard_data=json.dumps(leaderboards)
                    )
                else:
                    leaderboards = json.loads(leaderboards_cache.leaderboard_data)

        leaderboard = leaderboards.get(leaderboard_key, [])
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

    async def get_playing_history(self, period: str) -> PlayingHistory | None:
        now = datetime.now(tz=UTC)

        async with self._pool.acquire() as conn:
            if period == PLAYING_ALL_TIME:
                first = await get_first_game_stats(conn)
                if not first:
                    return None
                since = first.recorded_at
                # buckets must divide a day evenly, otherwise the daily player
                # cycle aliases into a fake zigzag
                hours = (now - since).total_seconds() / 3600
                bucket_hours = math.ceil(hours / _ALL_TIME_TARGET_BUCKETS)
                if bucket_hours > 6:
                    bucket_hours = math.ceil(bucket_hours / 24) * 24
                else:
                    bucket_hours = next(h for h in (1, 2, 3, 6) if h >= bucket_hours)
                bucket_seconds = bucket_hours * 3600
            else:
                span, bucket_seconds = PLAYING_PERIODS[period]
                since = now - span

            rows = await get_playing_history(
                conn, bucket_seconds=bucket_seconds, since=since
            )
            peak = await get_playing_peak(conn, recorded_at=since)
            lowest = await get_playing_low(conn, recorded_at=since)
        if not rows or not peak or not lowest:
            return None

        # fill missing buckets with None so downtime shows as a gap in the graph
        by_bucket = {int(row.bucket.timestamp()): row for row in rows}
        history = PlayingHistory([], [], [], [], peak=peak, lowest=lowest)
        bucket = int(since.timestamp()) // bucket_seconds * bucket_seconds
        while bucket <= now.timestamp():
            row = by_bucket.get(bucket)
            history.times.append(datetime.fromtimestamp(bucket, tz=UTC))
            history.averages.append(row.avg_playing if row else None)
            history.lows.append(row.min_playing if row else None)
            history.highs.append(row.max_playing if row else None)
            bucket += bucket_seconds

        return history

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

        if not await self._remove_from_top10_leaderboards(source_user.id):
            _logger.error(
                "failed to transfer stats - problem removing source from top 10 leaderboards"
            )
            return False

        return True

    async def _remove_from_top10_leaderboards(self, user_id: int) -> bool:
        top10 = await self._leaderboard_client.get_live_leaderboards_top10()
        if not top10:
            return False

        removed_total = 0
        for period in ("AllTime", "Monthly", "Yearly"):
            for stat_key, entries in top10.get(period, {}).items():
                kept = [e for e in entries if int(e["UserId"]) != int(user_id)]
                removed = len(entries) - len(kept)
                if not removed:
                    continue
                # placeholders go last so the list stays sorted
                kept += [{"Count": 0, "UserId": 1} for _ in range(removed)]
                top10[period][stat_key] = kept
                removed_total += removed

        if not removed_total:
            return True
        return await self._leaderboard_client.set_live_leaderboards_top10(top10)
