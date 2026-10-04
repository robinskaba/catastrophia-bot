from datetime import datetime

import aiohttp
import asyncpg

from src.common.db.username_cache import get_cached_username, upsert_username
from src.features.users.clients.restrictions_client import RestrictionsClient
from src.features.users.clients.spender_client import SpenderClient
from src.features.users.clients.user_client import UserClient
from src.features.users.model.restriction import Restriction
from src.features.users.model.roblox_user import RobloxUser
from src.features.users.model.user import User


class UserService:

    def __init__(self, session: aiohttp.ClientSession, pool: asyncpg.Pool):
        self._pool = pool

        self._user_client = UserClient(session)
        self._restrictions_client = RestrictionsClient(session)
        self._spender_client = SpenderClient(session)

    async def get_user(self, username: str) -> User | None:
        present_user = await self._user_client.get_user_from_username(username)
        # cache username
        if present_user:
            async with self._pool.acquire() as conn:
                await upsert_username(
                    conn, user_id=present_user.id, username=present_user.name
                )
        return present_user

    async def get_roblox_user_by_id(self, user_id: int) -> RobloxUser | None:
        return await self._user_client.get_roblox_user(user_id)

    async def get_username(self, user_id: int) -> str | None:
        async with self._pool.acquire() as conn:
            cached_user = await get_cached_username(conn, user_id=user_id)
            if (
                not cached_user
                or not cached_user.updated_at
                or (
                    datetime.now(tz=cached_user.updated_at.tzinfo)
                    - cached_user.updated_at
                ).days
                > 7
            ):
                present_user = await self._user_client.get_roblox_user(user_id)
                if not present_user:
                    return None
                await upsert_username(conn, user_id=user_id, username=present_user.name)
                return present_user.name
        return cached_user.username

    async def get_user_thumbnail_url(self, user: User) -> str:
        return await self._user_client.get_user_avatar_headshot_img_url(user.id)

    async def get_user_restrictions(self, user: User) -> list[Restriction] | None:
        return await self._restrictions_client.get_user_restrictions(user.id)

    async def get_robux_spent(self, user: User) -> int:
        return await self._spender_client.get_robux_spent(user.name)

    async def set_robux_spent(self, user: User, amount: int) -> bool:
        return await self._spender_client.set_robux_spent(user.name, amount)

    async def add_user_restriction(
        self, user: User, reason: str, duration_in_hours: int, ban_alts=True
    ) -> bool:
        return await self._restrictions_client.add_user_restriction(
            user.id, reason, duration_in_hours, not ban_alts
        )

    async def remove_user_restriction(self, user: User) -> bool:
        return await self._restrictions_client.remove_user_restriction(user.id)
