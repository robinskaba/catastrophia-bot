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
        self._user_client = UserClient()
        self._restrictions_client = RestrictionsClient()
        self._spender_client = SpenderClient()

    def get_user(self, username: str) -> User | None:
        return self._user_client.get_user_from_username(username)

    def get_detailed_user(self, user_id: str) -> RobloxUser | None:
        return self._user_client.get_roblox_user(user_id)

    def get_user_thumbnail_url(self, user: User) -> str:
        return self._user_client.get_user_avatar_headshot_img_url(user.id)

    def get_user_restrictions(self, user: User) -> list[Restriction] | None:
        return self._restrictions_client.get_user_restrictions(user.id)

    def get_robux_spent(self, user: User) -> int:
        return self._spender_client.get_roblox_spent(user.name)

    def add_user_restriction(
        self, user: User, reason: str, duration_in_days: int, ban_alts=True
    ) -> bool:
        return self._restrictions_client.add_user_restriction(
            user.id, reason, duration_in_days, not ban_alts
        )

    def remove_user_restriction(self, user: User) -> bool:
        return self._restrictions_client.remove_user_restriction(user.id)
