from datetime import datetime

import aiohttp
import asyncpg
from discord import user

from src.common.db.username_cache import get_cached_username, upsert_username
from src.features.users.clients.restrictions_client import RestrictionsClient
from src.features.users.clients.spender_client import SpenderClient
from src.features.users.model.restriction import Restriction
from src.features.users.model.roblox_user import RobloxUser
from src.features.users.model.user import User
from src.features.users.clients.user_client import UserClient


class UserService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._pool = None

        self._user_client = UserClient()
        self._restrictions_client = RestrictionsClient()
        self._spender_client = SpenderClient()

    def set_session(self, session: aiohttp.ClientSession):
        self._user_client.set_session(session)
        self._restrictions_client.set_session(session)
        self._spender_client.set_session(session)

    def set_pool(self, pool: asyncpg.Pool):
        self._pool = pool

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
        return await self._spender_client.get_roblox_spent(user.name)

    async def add_user_restriction(
        self, user: User, reason: str, duration_in_hours: int, ban_alts=True
    ) -> bool:
        return await self._restrictions_client.add_user_restriction(
            user.id, reason, duration_in_hours, not ban_alts
        )

    async def remove_user_restriction(self, user: User) -> bool:
        return await self._restrictions_client.remove_user_restriction(user.id)
