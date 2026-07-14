import requests

from src.features.users.model.roblox_user import RobloxUser
from src.common.http.base_client import BaseClient
from src.features.users.model.user import User


class UserClient(BaseClient):

    def __init__(self):
        super().__init__()

        self._users_endpoint = self.base_endpoint + "/users"

    def get_roblox_user(self, user_id: str) -> RobloxUser | None:
        endpoint = f"{self._users_endpoint}/{user_id}"
        response = requests.get(url=endpoint, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return None

        return RobloxUser.from_dict(response.json())

    def get_user_from_username(self, username: str) -> User | None:
        endpoint = "https://users.roblox.com/v1/usernames/users"
        payload = {"usernames": [username], "excludeBannedUsers": False}
        response = requests.post(url=endpoint, json=payload)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return None

        data: list = response.json()["data"]
        if len(data) < 1:
            return None
        return User.from_dict(data[0])

    def get_user_avatar_headshot_img_url(self, user_id: str) -> str:
        endpoint = "https://thumbnails.roblox.com/v1/users/avatar-headshot"
        params = {
            "userIds": user_id,
            "size": "420x420",
            "format": "Png",
            "isCircular": False,
        }
        response = requests.get(url=endpoint, params=params)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            return ""

        data = response.json()
        thumbnail_url = data["data"][0]["imageUrl"]

        return thumbnail_url
