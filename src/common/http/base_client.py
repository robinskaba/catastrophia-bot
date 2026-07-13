from src.common.config.config import Env


class BaseClient:

    def __init__(self):
        api_key = Env.API_KEY
        self.headers = {"x-api-key": api_key}
        self.base_endpoint = f"https://apis.roblox.com/cloud/v2"
