import aiohttp

from src.features.users.model.roblox_user import RobloxUser
from src.common.http.base_client import BaseClient
from src.features.users.model.user import User


class UserClient(BaseClient):

    def __init__(self):
        super().__init__()

        self._users_endpoint = self.base_endpoint + "/users"

    async def get_roblox_user(self, user_id: str) -> RobloxUser | None:
        endpoint = f"{self._users_endpoint}/{user_id}"

        try:
            async with self._session.get(
                url=endpoint, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return None

        return RobloxUser.from_dict(data)

    async def get_user_from_username(self, username: str) -> User | None:
        endpoint = "https://users.roblox.com/v1/usernames/users"
        payload = {"usernames": [username], "excludeBannedUsers": False}

        try:
            async with self._session.post(url=endpoint, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return None

        names: list = data["data"]
        if len(names) < 1:
            return None
        return User.from_dict(names[0])

    async def get_user_avatar_headshot_img_url(self, user_id: str) -> str:
        endpoint = "https://thumbnails.roblox.com/v1/users/avatar-headshot"
        params = {
            "userIds": user_id,
            "size": "420x420",
            "format": "Png",
            "isCircular": "false",
        }

        try:
            async with self._session.get(url=endpoint, params=params) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as _:
            return ""

        return data["data"][0]["imageUrl"]
