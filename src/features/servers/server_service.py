import aiohttp

from src.features.servers.server_client import ServerClient
from src.features.servers.server_model import ServerStateMS, ServerStateMSG


class ServerService:

    def __init__(self):
        self._server_client = ServerClient()

    def set_session(self, session: aiohttp.ClientSession):
        self._server_client.set_session(session)

    async def open_server_for_tournament(self, server_code: int) -> bool:
        msgs_success = await self._server_client.send_server_access_msg(
            server_code, ServerStateMSG.TOURNAMENT
        )
        if not msgs_success:
            return False
        ms_success = await self._server_client.save_server_access_to_memory_store(
            server_code, ServerStateMS.TOURNAMENT
        )
        return ms_success

    async def end_tournament_and_restart(self, server_code: int) -> bool:
        msgs_success = await self._server_client.send_server_access_msg(
            server_code, ServerStateMSG.RESTART
        )
        if not msgs_success:
            return False
        ms_success = await self._server_client.save_server_access_to_memory_store(
            server_code, ServerStateMS.RECHARING
        )
        return ms_success
