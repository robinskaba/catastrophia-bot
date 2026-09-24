from __future__ import annotations


class User:

    def __init__(self, id: int, name: str, display_name: str):
        self.id = id
        self.name = name
        self.display_name = display_name

    @staticmethod
    def from_dict(response: dict) -> User:
        return User(
            id=int(response["id"]),
            name=response["name"],
            display_name=response["displayName"],
        )
