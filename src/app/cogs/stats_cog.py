import json
import logging
from discord import Color, Embed, Interaction, Member, Object
from discord.app_commands import command
from discord.ext import commands, tasks
from src.core.services.user_service import UserService
from src.config.config import Config
from src.core.services.stats_service import StatsService
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _is_confidential(username: str) -> bool:
    return username.lower() in Config.CONFIDENTIAL_USERNAMES


def _is_owner(member: Member) -> bool:
    return member.get_role(Config.OWNER_ROLE_ID) != None


with open("assets/leaderboards.json", "r") as read:
    data = json.load(read)
    _LEADERBOARD_NAME_ORDER = data["print_order"]
    _LEADERBOARD_FULL_NAMES = data["names"]


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
                logger.error(f"missing Playing channel: {e}")

        if visits_vc:
            visits_count = f"{game_stats.visits / 1_000_000:.2f}M"
            try:
                await visits_vc.edit(name=f"Visits: {visits_count}")
            except Exception as e:
                logger.error(f"missing Visits channel: {e}")

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
                logger.info("top playtimes already shown on bot start")
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

    @command(name="playtime", description="Shows the player's playtime.")
    async def playtime(self, interaction: Interaction, username: str) -> None:
        # don't allow regular players find playtime for owners
        if _is_confidential(username) and not _is_owner(interaction.user):
            await interaction.response.send_message(
                "This is confidential.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        user = self.user_service.get_user(username)
        playtime = self.stats_service.get_player_playtime(user.name) if user else 0
        username = user.name if user else username

        message = (
            f"{username} has played {playtime // 60} hours and {playtime % 60} minutes."
            if playtime >= 60
            else f"{username} has played less than 1 hour."
        )
        embed = Embed(title="", description=message, color=Color.blue())

        await interaction.followup.send(embed=embed)

    @command(name="stats", description="Shows the player's leaderboards stats.")
    async def stats(self, interaction: Interaction, username: str) -> None:
        # don't allow regular players find playtime for owners
        if _is_confidential(username) and not _is_owner(interaction.user):
            await interaction.response.send_message(
                "This is confidential.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        user = self.user_service.get_user(username)
        if not user:
            await interaction.followup.send(
                embed=Embed(
                    title=f"{username}'s leaderboard stats",
                    description="This player does not exist.",
                    color=Color.red(),
                )
            )
            return
        stats = self.stats_service.get_player_stats(user.id)

        embed = Embed(title=f"{user.name}'s leaderboard stats", color=Color.green())
        embed.set_thumbnail(url=self.user_service.get_user_thumbnail_url(user))

        for leadeboard_key in _LEADERBOARD_NAME_ORDER:
            value = stats.get(leadeboard_key)
            value = (
                value if value else 0
            )  # either error occurred, player has no stats recorded or key does not exist

            full_name = _LEADERBOARD_FULL_NAMES.get(leadeboard_key)
            full_name = full_name if full_name else leadeboard_key

            pretty_value = f"{value:,}".replace(",", " ")  # format to 100 000 000

            embed.add_field(
                name=full_name,
                value=f"{pretty_value}",
                inline=True,
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatsCog(bot), guilds=[Object(id=bot.guild_id)])
