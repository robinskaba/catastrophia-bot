import re
from discord import Message, Object
from discord.ext import commands

from src.config.config import Config


class FilterCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self._youtube_videos_channel_id = Config.YOUTUBE_VIDEOS_CHANNEL_ID

        self._youtube_regex = re.compile(
            r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+"
        )

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:  # to prevent infinite loop
            return

        match message.channel.id:
            case self._youtube_videos_channel_id:
                await self.enforce_youtube_videos(message)

    async def enforce_youtube_videos(self, message):
        """Delete messages in #youtube-videos if they are not a youtube link."""

        if not self._youtube_regex.search(message.content):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, this channel is for **youtube videos only!**",
                delete_after=10,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FilterCog(bot), guilds=[Object(id=bot.guild_id)])
