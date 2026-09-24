import logging
import time
import asyncpg

from src.common.db import models
from src.common.db.creators import add_creator, get_creator

_logger = logging.getLogger(__name__)


class CreatorService:

    def __init__(self):
        self._pool = None

    def set_pool(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_or_create(self, discord_id: int) -> models.Creator:
        async with self._pool.acquire() as conn:
            creator = await get_creator(conn=conn, discord_id=discord_id)
            if not creator:
                _logger.info(f"new creator detected: {discord_id}")
                creator = await add_creator(
                    conn=conn, discord_id=discord_id, since=time.time()
                )
        return creator
