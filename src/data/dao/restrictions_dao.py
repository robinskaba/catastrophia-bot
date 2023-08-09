from discord import datetime
import requests
from src.data.model.restriction import Restriction
from src.data.dao.experience_dao import ExperienceDao


class RestrictionsDao(ExperienceDao):

    def __init__(self):
        super().__init__()

        self.user_restriction_endpoint = f"{self.base_endpoint}/user-restrictions"

    def get_user_restrictions(self, user_id: str) -> list[Restriction] | None:
        endpoint = f"{self.user_restriction_endpoint}:listLogs"
        params = {"filter": f"user == 'users/{user_id}'"}
        response = requests.get(url=endpoint, params=params, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(e)
            return None

        logs = response.json()["logs"]
        restrictions = []
        for log in logs:
            reason = log.get("privateReason", "Unknown Reason")
            date_str = log["createTime"]
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            duration = log.get("duration")
            active = log.get("active")
            if duration:
                duration = duration[:-1]
                duration = int(duration)

            restrictions.append(Restriction(date, duration, active, reason))

        return restrictions

    def add_user_restriction(
        self, user_id: str, reason: str, duration_in_days: int | None, exclude_alt=False
    ) -> bool:
        endpoint = f"{self.user_restriction_endpoint}/{user_id}"
        data = {
            "gameJoinRestriction": {
                "active": True,
                "privateReason": f"{reason} (from DC)",
                "displayReason": "Cheating",
                "excludeAltAccounts": exclude_alt,
            }
        }
        if duration_in_days:
            data["gameJoinRestriction"]["duration"] = f"{duration_in_days * 24 * 3600}s"

        response = requests.patch(url=endpoint, json=data, headers=self.headers)
        try:
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as err:
            print(f"Error: {err}")
            return False

    def remove_user_restriction(self, user_id: str) -> bool:
        endpoint = f"{self.user_restriction_endpoint}/{user_id}"

        data = {
            "gameJoinRestriction": {
                "active": False,
                "privateReason": "unbanned (from DC)",
            }
        }

        response = requests.patch(url=endpoint, json=data, headers=self.headers)
        try:
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as err:
            print(f"Error: {err}")
            return False
