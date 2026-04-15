import datetime
import logging
from discord import Interaction, Member, Object, TextChannel, User, app_commands
import discord
from discord.app_commands import Choice
from discord.ext import commands

logger = logging.getLogger(__name__)


class ManagerCog(commands.Cog):
    """Cog with commands to manage the Discord server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Clears last messages from a user.")
    async def clear_messages(
        self,
        interaction: Interaction,
        user: User,
        channel: TextChannel,
        limit: int = 100,
    ) -> None:
        """Removes messages from a user."""
        await interaction.response.defer(ephemeral=True)

        two_weeks_ago = discord.utils.utcnow() - datetime.timedelta(weeks=2)
        searched_messages_limit = (
            limit * 3 if limit < 100 else None
        )  # allow max search if limit set to 100

        user_messages = []
        async for message in channel.history(limit=searched_messages_limit):
            if message.created_at < two_weeks_ago:
                break

            if len(user_messages) >= limit:
                break

            if message.author == user:
                user_messages.append(message)

        if user_messages:
            # message removal
            await channel.delete_messages(user_messages)

        await interaction.followup.send(
            f"```Removed {len(user_messages)} last message(s) from {user.display_name} ({user.name}) in #{channel.name}.```",
            ephemeral=True,
        )
        logger.info(
            f"removed {len(user_messages)} last message(s) from {user.display_name} ({user.name}) in #{channel.name}."
        )

    @app_commands.command(
        name="ban", description="Permanently bans a user from the discord server."
    )
    @app_commands.choices(
        delete_messages=[
            Choice(name="None", value=0),
            Choice(name="Last 10 minutes", value=600),
            Choice(name="Last hour", value=3600),
            Choice(name="Last 24 hours", value=86400),
            Choice(name="Last 2 days", value=172800),
            Choice(name="Last 7 days", value=604800),
        ]
    )
    async def ban(
        self,
        interaction: Interaction,
        user: User,
        delete_messages: Choice[int],
        reason: str | None = None,
    ):
        """Bans a user."""

        member: Member = interaction.channel.guild.get_member(user.id)

        await interaction.response.send_message(
            f"```Banned permanently {user.display_name} (@{user.name}) for {reason}.```",
            ephemeral=True,
        )

        await member.ban(delete_message_seconds=delete_messages.value, reason=reason)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ManagerCog(bot), guilds=[Object(id=bot.guild_id)])
