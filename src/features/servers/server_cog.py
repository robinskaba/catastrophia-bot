from asyncio import tasks
from datetime import datetime
import logging
from threading import local
from zoneinfo import ZoneInfo
from discord import (
    Color,
    Embed,
    Interaction,
    Object,
    app_commands,
)
from discord.ext import commands, tasks
from src.common.config.config import Config
from src.features.servers.server_service import ServerService

_logger = logging.getLogger(__name__)

local_tz = ZoneInfo(Config.TIMEZONE)
_FULL_STRF = "%d.%m.%Y %H:%M"

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


def _get_server_name(code: int) -> str | None:
    for name, val in Config.SERVERS.items():
        if val == code:
            return name
    return None


class ServerCog(commands.Cog):
    """Cog for handling Catastrophia servers."""

    def __init__(self, bot: commands.Bot):
        self._bot = bot

        self._server_service = ServerService()

    async def cog_load(self):
        self._server_service.set_session(self._bot.session)
        self._server_service.set_pool(self._bot.pool)

        self.handle_scheduled_tournaments.start()

    async def cog_unload(self):
        self.handle_scheduled_tournaments.stop()

    @tasks.loop(minutes=1)
    async def handle_scheduled_tournaments(self):
        await self._server_service.handle_scheduled_tournaments()

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
        success = await self._server_service.start_tournament(code)

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
        success = await self._server_service.end_tournament(code)

        title = (
            f"Ended the tournament on {server_name} ({server})"
            if success
            else f"Failed to end the tournament on {server_name}"
        )
        embed = Embed(title=title, color=Color.green() if success else Color.red())
        await interaction.followup.send(embed=embed, ephemeral=is_ephemeral)

    @app_commands.command(
        name="schedule-tournament", description="Schedules a tournament on a server."
    )
    @app_commands.describe(
        server="Server name abbreviation",
        when=f"Format: DD.MM. HH:MM",
    )
    async def schedule_tournament(
        self,
        interaction: Interaction,
        server: str,
        when: str,
        duration_in_minutes: int | None,
    ):
        ephemeral = True
        await interaction.response.defer(ephemeral=ephemeral)
        server_name = _shortcut_to_server_name(server)
        code = _get_server_code(server_name)
        if not code:
            await interaction.followup.send(
                content="Unknown server", ephemeral=ephemeral
            )
            return

        date, time = when.split(" ")
        when = (
            f"{date}{datetime.now().year} {time}"  # insert automatically current year
        )

        when_dt = datetime.strptime(when, _FULL_STRF)
        success = await self._server_service.schedule_tournament(
            code, when_dt, duration_in_minutes
        )

        title = (
            f"{server_name} tournament scheduled at {when}"
            if success
            else f"Failed to schedule the tournament."
        )
        embed = Embed(title=title, color=Color.green() if success else Color.red())
        await interaction.followup.send(embed=embed, ephemeral=ephemeral)

    @app_commands.command(
        name="list-scheduled-tournaments",
        description="Lists upcoming or on-going tournaments.",
    )
    async def list_scheduled_tournaments(self, interaction: Interaction):
        ephemeral = True
        await interaction.response.defer(ephemeral=ephemeral)

        tournaments = await self._server_service.get_upcoming_tournaments()

        if len(tournaments) > 0:
            out = ""
            for tour in tournaments:
                server_name = _get_server_name(tour.server_code)
                ends_at = (
                    tour.ends_at.astimezone(local_tz).strftime(_FULL_STRF)
                    if tour.ends_at
                    else None
                )
                out += f"{server_name}: {tour.scheduled_at.astimezone(local_tz).strftime(_FULL_STRF)}{ ' - ' + ends_at if ends_at else ''}\n"
        else:
            out = "No scheduled tournaments"

        embed = Embed(
            title="Upcoming tournaments", description=out, color=Color.yellow()
        )
        await interaction.followup.send(embed=embed, ephemeral=ephemeral)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerCog(bot), guilds=[Object(id=bot.guild_id)])
