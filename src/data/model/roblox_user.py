from __future__ import annotations
from datetime import datetime
from src.data.model.user import User


class RobloxUser(User):
    def __init__(
        self,
        create_time: datetime,
        user_id: str,
        name: str,
        display_name: str,
        about: str,
        locale: str,
        premium: bool,
        id_verified: bool,
    ):
        super().__init__(user_id, name, display_name)

        self._create_time = create_time
        self.about = about
        self.locale = locale
        self.premium = premium
        self.id_verified = id_verified

    @staticmethod
    def from_dict(data: dict) -> RobloxUser:
        return RobloxUser(
            create_time=datetime.fromisoformat(
                data.get("createTime", "").replace("Z", "+00:00")
            ),
            user_id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("displayName", ""),
            about=data.get("about", ""),
            locale=data.get("locale", ""),
            premium=data.get("premium", None),
            id_verified=data.get("idVerified", None),
        )

    @property
    def account_age_in_days(self) -> int:
        """Calculate account age in days."""
        return (datetime.now(self._create_time.tzinfo) - self._create_time).days
