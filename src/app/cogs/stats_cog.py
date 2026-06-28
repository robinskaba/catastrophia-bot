import calendar
import json
import logging
from discord import Color, Embed, Interaction, Member, Object
from discord.app_commands import autocomplete, choices, command, describe, Choice
from discord.ext import commands, tasks
from src.config.config import Config
from datetime import UTC, datetime, timezone

from src.core.stats.stats_service import StatsService
from src.core.users.user_service import UserService

_logger = logging.getLogger(__name__)


def _is_confidential(username: str) -> bool:
    return username.lower() in Config.CONFIDENTIAL_USERNAMES


def _is_owner(member: Member) -> bool:
    return member.get_role(Config.OWNER_ROLE_ID) != None


with open("assets/leaderboards.json", "r") as read:
    data = json.load(read)
    _LEADERBOARD_NAME_ORDER = data["print_order"]
    _LEADERBOARD_FULL_NAMES = data["names"]

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

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.stats_service = StatsService()
        self.user_service = UserService()

    async def cog_load(self):
        self.show_top_playtimes.start()
        self.update_game_stats.start()

    async def cog_unload(self):
        self.show_top_playtimes.cancel()
        self.update_game_stats.cancel()

    @tasks.loop(minutes=10)
    async def update_game_stats(self):
        game_stats = self.stats_service.get_game_stats()
        if not game_stats:
            return

        playing_vc = self.bot.get_channel(Config.PLAYING_CHANNEL_ID)
        visits_vc = self.bot.get_channel(Config.VISITS_CHANNEL_ID)

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
        top_players_channel = self.bot.get_channel(Config.TOP_PLAYERS_CHANNEL_ID)
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

        top_times: list[tuple] = self.stats_service.get_top_playtimes()
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

            embed = Embed(
                title=title,
                description=description_text,
                color=Color.gold(),
            )

            await top_players_channel.send(embed=embed)

    @show_top_playtimes.before_loop
    @update_game_stats.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()

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
            await interaction.followup.send_message("This is confidential.")
            return

        title_range_suffix = _range_suffix(month=month, year=year)
        user = self.user_service.get_user(username)
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
        stats = self.stats_service.get_player_stats(user.id, month=month, year=year)
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
        embed.set_thumbnail(url=self.user_service.get_user_thumbnail_url(user))
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
        top10 = self.stats_service.get_top_leaderboard(
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

        embed = Embed(title=title, description=leaderboard_txt, color=Color.yellow())
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatsCog(bot), guilds=[Object(id=bot.guild_id)])
