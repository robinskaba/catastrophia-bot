import discord
from discord.ext import commands, tasks
from discord import Object
from datetime import datetime, timezone, timedelta

from src.config.config import Config


class TicketCog(commands.Cog):
    """Cog to handle ticket channels made by 3rd party bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.tickets_category_id = Config.TICKETS_CATEGORY_ID
        self.excluded_ticket_channels = Config.EXCLUDED_TICKET_CHANNELS
        self.max_inactivity = timedelta(days=Config.TICKET_MAX_INACTIVITY)  # in days

    async def cog_load(self):
        self.check_inactive_tickets.start()

    async def cog_unload(self):
        self.check_inactive_tickets.cancel()

    @tasks.loop(hours=1)
    async def check_inactive_tickets(self):
        tickets_category = self.bot.get_channel(self.tickets_category_id)
        if not isinstance(tickets_category, discord.CategoryChannel):
            raise KeyError(
                f"Category ID '{self.tickets_category_id}' is not a valid category!"
            )

        for channel in tickets_category.text_channels:
            if (
                channel.name in self.excluded_ticket_channels
            ):  # dont remove public channels
                continue

            try:
                messages = [message async for message in channel.history(limit=1)]

                # if the channel has NO messages at all then keep it
                # does not apply to tickets where no message was sent, because those have the message by ticket bot
                if not messages:
                    continue

                last_msg = messages[0]

                # calculating time difference (discord uses UTC)
                now = datetime.now(timezone.utc)
                time_diff = now - last_msg.created_at

                if time_diff > self.max_inactivity:
                    print(
                        f"Closing {channel.name}: Inactive for {time_diff.days} days."
                    )

                    # delete channel because it was inactive
                    await channel.delete(
                        reason=f"Ticket inactive for > {self.max_inactivity} days"
                    )

            except Exception as e:
                print(f"Error checking channel {channel.name}: {e}")

    @check_inactive_tickets.before_loop
    async def before_check_tickets(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TicketCog(bot), guilds=[Object(id=bot.guild_id)])
