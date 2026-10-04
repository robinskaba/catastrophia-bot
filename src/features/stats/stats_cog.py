import calendar
import json
import logging
from datetime import UTC, datetime, timezone

from discord import Color, Embed, Interaction, Member, Object, app_commands
from discord.app_commands import (
    Choice,
    autocomplete,
    choices,
    command,
    describe,
    rename,
)
from discord.ext import commands, tasks

from src.common.bot import CatastrophiaBot
from src.common.config.config import Config
from src.common.utils.graphing import create_line_graph

_logger = logging.getLogger(__name__)


def _is_confidential(username: str) -> bool:
    return username.lower() in Config.CONFIDENTIAL_USERNAMES


def _is_owner(member: Member) -> bool:
    return member.get_role(Config.OWNER_ROLE_ID) != None


with open("assets/leaderboards.json", "r") as read:
    _data = json.load(read)
    _LEADERBOARD_NAME_ORDER = [item["id"] for item in _data]
    _LEADERBOARD_FULL_NAMES = {item["id"]: item["name"] for item in _data}
    _LEADERBOARD_COLORS = {item["id"]: item.get("color", "#5865F2") for item in _data}

_MONTHS_CHOICES = [
    Choice(name="January", value=1),
    Choice(name="February", value=2),
    Choice(name="March", value=3),
    Choice(name="April", value=4),
    Choice(name="May", value=5),
    Choice(name="June", value=6),
    Choice(name="July", value=7),
    Choice(name="August", value=8),
    Choice(name="September", value=9),
    Choice(name="October", value=10),
    Choice(name="November", value=11),
    Choice(name="December", value=12),
]

_LEADERBOARD_CHOICES = [
    Choice(name=_LEADERBOARD_FULL_NAMES[key], value=key)
    for key in _LEADERBOARD_NAME_ORDER
]


async def _year_choices(interaction: Interaction, current: int) -> list[Choice[int]]:
    current_date = datetime.now(tz=UTC)
    return [
        Choice(name=year, value=year) for year in range(2026, current_date.year + 1)
    ]


def _range_suffix(month: int | None, year: int | None) -> str:
    if month:
        return f" for {calendar.month_name[month]} {year}"
    elif year:
        return f" for {year}"
    return ""


def _format_leaderboard_value(leaderboard: str, value: int) -> str:
    if leaderboard == "Playtime":
        if value < 60:
            return "less than 1 hour"
        else:
            return f"{value // 60} hours and {value % 60} minutes"
    else:
        return f"{value:,}".replace(",", " ")  # format to 100 000 000


class StatsCog(commands.Cog):

    def __init__(self, bot: CatastrophiaBot):
        self._bot = bot

    async def cog_load(self):
        self.show_top_playtimes.start()
        self.update_game_stats.start()
        self.record_game_stats.start()

    async def cog_unload(self):
        self.show_top_playtimes.cancel()
        self.update_game_stats.cancel()
        self.record_game_stats.cancel()

    @tasks.loop(seconds=30)
    async def record_game_stats(self):
        await self._bot.stats_service.record_game_stats()

    @tasks.loop(minutes=15)
    async def update_game_stats(self):
        game_stats = await self._bot.stats_service.get_game_stats()
        if not game_stats:
            return

        playing_vc = self._bot.get_channel(Config.PLAYING_CHANNEL_ID)
        visits_vc = self._bot.get_channel(Config.VISITS_CHANNEL_ID)

        if playing_vc:
            try:
                await playing_vc.edit(name=f"Playing: {game_stats.playing}")
            except Exception as e:
                _logger.error(f"missing Playing channel: {e}")

        if visits_vc:
            visits_count = f"{game_stats.visits / 1_000_000:.2f}M"
            try:
                await visits_vc.edit(name=f"Visits: {visits_count}")
            except Exception as e:
                _logger.error(f"missing Visits channel: {e}")

    @tasks.loop(hours=24)
    async def show_top_playtimes(self):
        top_players_channel = self._bot.get_channel(Config.TOP_PLAYERS_CHANNEL_ID)
        if not top_players_channel:
            _logger.warning("missing top players channel")
            return
        messages = [message async for message in top_players_channel.history(limit=1)]
        last_msg = messages[0] if messages and len(messages) > 0 else None
        if last_msg:
            created_seconds_ago = (
                datetime.now(timezone.utc) - last_msg.created_at
            ).total_seconds()
            if created_seconds_ago < 23 * 3600:
                _logger.info("top playtimes already shown on bot start")
                return

        await top_players_channel.purge()

        top_times: list[tuple] = await self._bot.stats_service.get_top_playtimes()
        entries_per_block = 20
        for i in range(0, len(top_times), entries_per_block):
            batch = top_times[i : i + entries_per_block]

            lines = []
            for index, entry in enumerate(batch):
                username, playtime = entry
                rank = i + index + 1

                hours = playtime // 60
                minutes = playtime % 60

                lines.append(
                    f"{rank}. **{username}**: {hours} hours and {minutes} minutes"
                )

            description_text = "\n".join(lines)
            title = "Top playtimes" if i == 0 else ""

            hex_color = _LEADERBOARD_COLORS.get("Playtime", "#5865F2")
            discord_color = Color.from_str(hex_color)

            embed = Embed(
                title=title,
                description=description_text,
                color=discord_color,
            )

            await top_players_channel.send(embed=embed)

    @show_top_playtimes.before_loop
    @update_game_stats.before_loop
    async def before_tasks(self):
        await self._bot.wait_until_ready()

    @command(name="stats", description="Shows the player's statistics.")
    @describe(
        username="Whose stats to display (case insensitive).",
        year="Unspecified year or month means all time statistics.",
    )
    @choices(month=_MONTHS_CHOICES)
    @autocomplete(year=_year_choices)
    async def stats(
        self,
        interaction: Interaction,
        username: str,
        year: int | None,
        month: int | None,
    ) -> None:
        await interaction.response.defer()

        if month and not year:
            year = datetime.now(tz=UTC).year

        # don't allow regular players find playtime for owners
        if _is_confidential(username) and not _is_owner(interaction.user):
            await interaction.followup.send("This is confidential.")
            return

        title_range_suffix = _range_suffix(month=month, year=year)
        user = await self._bot.user_service.get_user(username)
        if not user:
            await interaction.followup.send(
                embed=Embed(
                    title=f"{username}'s stats{title_range_suffix}",
                    description="This player does not exist.",
                    color=Color.red(),
                )
            )
            return

        title = f"{user.name}'s stats{title_range_suffix}"
        stats = await self._bot.stats_service.get_player_stats_for_period(
            user.id, month=month, year=year
        )
        if not stats:
            await interaction.followup.send(
                embed=Embed(
                    title=title,
                    description="There are no stats for this period.",
                    color=Color.red(),
                )
            )
            return

        stats_txt = ""
        for leaderboard_key in _LEADERBOARD_NAME_ORDER:
            value = stats.get(leaderboard_key)
            value = (
                value if value else 0
            )  # either error occurred, player has no stats recorded or key does not exist
            full_name = _LEADERBOARD_FULL_NAMES.get(leaderboard_key)
            full_name = full_name if full_name else leaderboard_key

            stat_txt = f"**{full_name}**: "
            if leaderboard_key == "Playtime":
                if value < 60:
                    stat_txt += "less than 1 hour"
                else:
                    stat_txt += f"{value // 60} hours and {value % 60} minutes"
            else:
                stat_txt += f"{value:,}".replace(",", " ")  # format to 100 000 000
            stats_txt += stat_txt + "\n"
        stats_txt = stats_txt[:-1]  # rm \n

        embed = Embed(title=title, color=Color.green(), description=stats_txt)
        thumbnail_url = await self._bot.user_service.get_user_thumbnail_url(user)
        embed.set_thumbnail(url=thumbnail_url)
        await interaction.followup.send(embed=embed)

    @command(
        name="leaderboards", description="Shows the top 10 players on a leaderboard."
    )
    @describe(
        leaderboard="What leaderboard to display.",
        year="Unspecified year or month means all time leaderboard.",
    )
    @choices(leaderboard=_LEADERBOARD_CHOICES, month=_MONTHS_CHOICES)
    @autocomplete(year=_year_choices)
    async def leaderboards(
        self,
        interaction: Interaction,
        leaderboard: str,
        year: int | None,
        month: int | None,
    ):
        await interaction.response.defer()

        if month and not year:
            year = datetime.now(tz=UTC).year

        title_range_suffix = _range_suffix(month=month, year=year)
        leaderboard_full_name = _LEADERBOARD_FULL_NAMES.get(
            leaderboard, "Invalid leaderboard"
        )
        title = f"Most {leaderboard_full_name.lower()}{title_range_suffix}"
        top10 = await self._bot.stats_service.get_top_leaderboard(
            leaderboard, month=month, year=year
        )
        if not top10:
            await interaction.followup.send(
                embed=Embed(
                    title=title,
                    description="There are no leaderboards for this period.",
                    color=Color.red(),
                )
            )
            return

        leaderboard_txt = ""
        for i, ranking in enumerate(top10):
            username, value = ranking
            value_txt = _format_leaderboard_value(leaderboard, value)
            line = f"{i + 1}. {username}: {value_txt}"
            leaderboard_txt += f"{line}\n"
        leaderboard_txt = leaderboard_txt[:-1]

        hex_color = _LEADERBOARD_COLORS.get(leaderboard, "#5865F2")
        discord_color = Color.from_str(hex_color)

        embed = Embed(title=title, description=leaderboard_txt, color=discord_color)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="transfer-stats",
        description="Transfers playtime and leaderboards stats from one account to another (overwrites target stats).",
    )
    async def transfer_stats(
        self, interaction: Interaction, source_username: str, target_username: str
    ):
        ephemeral = True
        await interaction.response.defer(ephemeral=ephemeral)
        ok = await self._bot.stats_service.transfer_stats(
            source_username, target_username
        )
        if ok:
            embed = Embed(
                title="Transferring stats was successful", color=Color.green()
            )
        else:
            embed = Embed(
                title="Failed to transfer stats",
                # TODO add specific error message in description
                color=Color.red(),
            )
        await interaction.followup.send(embed=embed, ephemeral=ephemeral)

    @command(name="graphs", description="Shows a graph of player's stats.")
    @rename(stat_key="stat")
    @choices(stat_key=_LEADERBOARD_CHOICES)
    @describe(
        username="Whose stats to display (case insensitive).",
        stat_key="Stats to graph",
    )
    async def graphs(
        self, interaction: Interaction, username: str, stat_key: str
    ) -> None:
        await interaction.response.defer()

        if _is_confidential(username) and not _is_owner(interaction.user):
            await interaction.followup.send("This is confidential.")
            return

        user = await self._bot.user_service.get_user(username)
        username = user.name if user else username
        title = f"{username}'s {_LEADERBOARD_FULL_NAMES[stat_key].lower()}"
        if not user:
            await interaction.followup.send(
                embed=Embed(
                    title=title,
                    description="This player does not exist.",
                    color=Color.red(),
                )
            )
            return

        graph_data = await self._bot.stats_service.get_player_stats_graphed(
            user_id=user.id, stat_key=stat_key
        )
        if not graph_data:
            await interaction.followup.send(
                embed=Embed(
                    title=title, description="No statistics found.", color=Color.red()
                )
            )
            return

        months, values = graph_data

        # format x-axis (07_2026 -> Jul '26)
        formatted_months = [
            datetime.strptime(m, "%m_%Y").strftime("%b '%y") for m in months
        ]

        # formatting
        formatting_suffix = ""
        if stat_key == "Playtime":
            values = [x / 60 for x in values]
            formatting_suffix = "h"

        # draw graph
        hex_color = _LEADERBOARD_COLORS.get(stat_key, "#5865F2")
        discord_color = Color.from_str(hex_color)

        graph_file = await create_line_graph(
            title=title,
            x_data=formatted_months,
            y_data=values,
            color=hex_color,
            y_tick_suffix=formatting_suffix,
            x_tick_rotation=45 if len(formatted_months) > 5 else 0,
        )

        embed = Embed(color=discord_color)
        embed.set_image(url="attachment://graph.png")

        await interaction.followup.send(file=graph_file, embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatsCog(bot), guilds=[Object(id=bot.guild_id)])
