import json
import logging
import aiohttp
from src.common.config.config import Config, Env
from src.common.http.base_client import BaseClient
from src.features.servers.server_model import ServerStateMS, ServerStateMSG

_logger = logging.getLogger(__name__)


class ServerClient(BaseClient):

    def __init__(self):
        super().__init__()

    async def send_server_access_msg(
        self, server_code: int, state: ServerStateMSG
    ) -> bool:
        endpoint = f"https://apis.roblox.com/cloud/v2/universes/{Env.UNIVERSE_ID}:publishMessage"
        payload = {
            "topic": Config.SERVER_STATE_MSGS_TOPIC,
            "message": json.dumps([str(server_code), state.value]),
        }

        try:
            async with self._session.post(
                url=endpoint, headers=self.headers, json=payload
            ) as response:
                response.raise_for_status()
        except aiohttp.ClientError as e:
            _logger.error(f"failed to send server state to messaging service: {e}")
            return False
        return True

    async def save_server_access_to_memory_store(
        self, server_code: int, state: ServerStateMS
    ) -> bool:
        endpoint = f"https://apis.roblox.com/cloud/v2/universes/{Env.UNIVERSE_ID}/memory-store/sorted-maps/{Config.SERVER_STATE_MEMORY_STORE}/items/{server_code}"

        params = {
            "allowMissing": "true"
        }  # upsert -> converts to POST request if missing
        payload = {"value": state.value, "ttl": f"{24 * 60 * 60}s"}

        try:
            # 3. Change .post() to .patch()
            async with self._session.patch(
                url=endpoint, headers=self.headers, params=params, json=payload
            ) as response:
                response.raise_for_status()
        except aiohttp.ClientError as e:
            _logger.error(f"failed to update server state in memory store: {e}")
            return False
        return True
