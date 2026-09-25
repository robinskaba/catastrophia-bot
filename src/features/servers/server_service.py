from datetime import datetime, timedelta, timezone
from http import server
import logging
from threading import local
from zoneinfo import ZoneInfo

import aiohttp
import asyncpg

from src.common.config.config import Config
from src.common.db import models
from src.common.db.tournaments import (
    add_scheduled_tournament,
    get_upcoming_or_ongoing_tournaments,
    update_tournament_state,
)
from src.features.servers.server_client import ServerClient
from src.features.servers.server_model import ServerStateMS, ServerStateMSG

_logger = logging.getLogger(__name__)

local_tz = ZoneInfo(Config.TIMEZONE)


class ServerService:

    def __init__(self):
        self._pool = None
        self._server_client = ServerClient()

    def set_session(self, session: aiohttp.ClientSession):
        self._server_client.set_session(session)

    def set_pool(self, pool: asyncpg.Pool):
        self._pool = pool

    async def start_tournament(self, server_code: int) -> bool:
        # mark started tournament as scheduled
        async with self._pool.acquire() as conn:
            await add_scheduled_tournament(
                conn,
                server_code=server_code,
                scheduled_at=datetime.now(local_tz),
                ends_at=None,
                state=1,
            )
        return await self._open_server_for_tournament(server_code)

    async def end_tournament(self, server_code: int) -> bool:
        # mark tournaments on this server that have started in the past as ended if still ongoing
        tournaments = await self.get_upcoming_tournaments()
        now = datetime.now(timezone.utc)
        for tournament in tournaments:
            if (
                tournament.scheduled_at <= now and tournament.state == 1
            ):  # tournament started in the past but is still on-going
                await self._mark_tournament(tournament.id, 2)  # mark tournament as done
        return await self._end_tournament_and_restart(server_code)

    async def schedule_tournament(
        self, server_code: int, when: datetime, duration_in_minutes: int | None = None
    ) -> int:
        ends_at = (
            (when + timedelta(minutes=duration_in_minutes)).replace(tzinfo=local_tz)
            if duration_in_minutes
            else None
        )
        async with self._pool.acquire() as conn:
            try:
                await add_scheduled_tournament(
                    conn=conn,
                    server_code=server_code,
                    scheduled_at=when.replace(tzinfo=local_tz),
                    ends_at=ends_at,
                    state=0,
                )
            except Exception as e:
                _logger.error(f"failed to schedule tournament on {server_code}: {e}")
                return False
            _logger.info(
                f"scheduled tournament on {server_code} at {when.strftime('%d.%m.%Y %H:%M')}"
            )
            return True

    async def get_upcoming_tournaments(self) -> list[models.ScheduledTournament]:
        async with self._pool.acquire() as conn:
            tournaments = await get_upcoming_or_ongoing_tournaments(conn)
            return tournaments

    async def handle_scheduled_tournaments(self):
        tournaments = await self.get_upcoming_tournaments()
        now = datetime.now(timezone.utc)
        for tournament in tournaments:
            state = tournament.state  # 0 = scheduled, 1 = open, 2 = over
            is_over = tournament.ends_at and tournament.ends_at <= now
            if tournament.scheduled_at <= now and state == 0:
                # open server
                await self._open_server_for_tournament(tournament.server_code)
                _logger.info(
                    f"scheduled server open: {tournament.server_code=}, time={tournament.scheduled_at.astimezone(local_tz).strftime('%d.%m.%Y %H:%M')}"
                )
                await self._mark_tournament(tournament.id, 1)
            elif is_over and state == 1:
                # close server
                await self._end_tournament_and_restart(tournament.server_code)
                _logger.info(
                    f"scheduled server close: {tournament.server_code=}, time={tournament.ends_at.astimezone(local_tz).strftime('%d.%m.%Y %H:%M')}"
                )
                await self._mark_tournament(tournament.id, 2)

    async def _open_server_for_tournament(self, server_code: int) -> bool:
        msgs_success = await self._server_client.send_server_access_msg(
            server_code, ServerStateMSG.TOURNAMENT
        )
        if not msgs_success:
            return False
        ms_success = await self._server_client.save_server_access_to_memory_store(
            server_code, ServerStateMS.TOURNAMENT
        )
        return ms_success

    async def _end_tournament_and_restart(self, server_code: int) -> bool:
        msgs_success = await self._server_client.send_server_access_msg(
            server_code, ServerStateMSG.RESTART
        )
        if not msgs_success:
            return False
        ms_success = await self._server_client.save_server_access_to_memory_store(
            server_code, ServerStateMS.RECHARING
        )
        return ms_success

    async def _mark_tournament(self, tournament_id: int, state: int):
        async with self._pool.acquire() as conn:
            _logger.debug(f"tournament {tournament_id} marked as {state}")
            await update_tournament_state(conn, id_=tournament_id, state=state)
