import logging
from discord import (
    Color,
    Embed,
    Interaction,
    Object,
    app_commands,
)
from discord.ext import commands
from src.common.config.config import Config
from src.features.servers.server_service import ServerService

_logger = logging.getLogger(__name__)

# generate server name mappings
_maps = set()
for server in Config.SERVERS:
    _maps.add(server.split(" ")[0])


def _shortcut_to_server_name(shortcut: str) -> str | None:
    for game_map in _maps:
        identifier = game_map[0].lower()
        if shortcut[0] == identifier:
            return game_map + " " + shortcut.replace(identifier, "")
    return None


def _get_server_code(name: str) -> int | None:
    return Config.SERVERS.get(name)


class ServerCog(commands.Cog):
    """Cog for handling Catastrophia servers."""

    def __init__(self, bot: commands.Bot):
        self._bot = bot

        self._server_service = ServerService()

    async def cog_load(self):
        self._server_service.set_session(self._bot.session)

    @app_commands.command(
        name="start-tournament", description="Opens the server for a tournament."
    )
    async def start_tournament(self, interaction: Interaction, server: str) -> None:
        is_ephemeral = True
        await interaction.response.defer(ephemeral=is_ephemeral)

        server_name = _shortcut_to_server_name(server)
        code = _get_server_code(server_name)
        if not code:
            await interaction.followup.send(
                content="Unknown server", ephemeral=is_ephemeral
            )
            return
        success = await self._server_service.open_server_for_tournament(code)

        title = (
            f"Tournament started on {server_name} ({server})"
            if success
            else f"Failed to start a tournament on {server_name}"
        )
        embed = Embed(title=title, color=Color.green() if success else Color.red())

        await interaction.followup.send(embed=embed, ephemeral=is_ephemeral)

    @app_commands.command(
        name="end-tournament", description="Closes the server and recharges it."
    )
    async def end_tournament(self, interaction: Interaction, server: str) -> None:
        is_ephemeral = True
        await interaction.response.defer(ephemeral=is_ephemeral)

        server_name = _shortcut_to_server_name(server)
        code = _get_server_code(server_name)
        if not code:
            await interaction.followup.send(
                content="Unknown server", ephemeral=is_ephemeral
            )
            return
        success = await self._server_service.end_tournament_and_restart(code)

        title = (
            f"Ended the tournament on {server_name} ({server})"
            if success
            else f"Failed to end the tournament on {server_name}"
        )
        embed = Embed(title=title, color=Color.green() if success else Color.red())
        await interaction.followup.send(embed=embed, ephemeral=is_ephemeral)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerCog(bot), guilds=[Object(id=bot.guild_id)])
