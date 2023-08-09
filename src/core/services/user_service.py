from src.data.dao.spender_dao import SpenderDao
from src.data.model.roblox_user import RobloxUser
from src.data.model.restriction import Restriction
from src.data.dao.restrictions_dao import RestrictionsDao
from src.data.model.user import User
from src.data.dao.user_dao import UserDao


class UserService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.user_dao = UserDao()
        self.restrictions_dao = RestrictionsDao()
        self.spender_dao = SpenderDao()

    def get_user(self, username: str) -> User | None:
        return self.user_dao.get_user_from_username(username)

    def get_detailed_user(self, username: str) -> RobloxUser | None:
        return self.user_dao.get_roblox_user(username)

    def get_user_thumbnail_url(self, user: User) -> str:
        return self.user_dao.get_user_avatar_headshot_img_url(user.id)

    def get_user_restrictions(self, user: User) -> list[Restriction] | None:
        return self.restrictions_dao.get_user_restrictions(user.id)

    def get_robux_spent(self, user: User) -> int:
        return self.spender_dao.get_roblox_spent(user.name)

    def add_user_restriction(
        self, user: User, reason: str, duration_in_days: int, ban_alts=True
    ) -> bool:
        return self.restrictions_dao.add_user_restriction(
            user.id, reason, duration_in_days, not ban_alts
        )

    def remove_user_restriction(self, user: User) -> bool:
        return self.restrictions_dao.remove_user_restriction(user.id)
