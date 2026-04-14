import re
from discord import Message, Object
from discord.ext import commands

from src.config.config import Config

MEDIA_EXTENSIONS = (
    ".gif",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".mp4",
    ".webm",
    ".mov",
)


class FilterCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self._youtube_regex = re.compile(
            r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+"
        )
        self._media_regex = re.compile(
            r"\.(gif|png|jpe?g|webp|bmp|mp4|webm|mov)|tenor\.com/view|giphy\.com/media|imgur\.com",
            re.IGNORECASE,
        )

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:  # to prevent infinite loop
            return

        if message.channel.id in Config.NO_MEDIA_CHANNELS:
            if await self.enforce_no_media(message):
                return

        match message.channel.id:
            case Config.YOUTUBE_VIDEOS_CHANNEL_ID:
                await self.enforce_youtube_videos(message)

    async def enforce_youtube_videos(self, message):
        """Delete messages in #youtube-videos if they are not a youtube link."""

        if not self._youtube_regex.search(message.content):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, this channel is for **youtube videos only!**",
                delete_after=10,
            )

    async def enforce_no_media(self, message: Message) -> bool:
        has_media = False

        # filtrace priloh
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(MEDIA_EXTENSIONS):
                has_media = True
                break
            if attachment.content_type and (
                "image" in attachment.content_type.lower()
                or "video" in attachment.content_type.lower()
            ):
                has_media = True
                break

        # filtrace odkazu ve zprave
        if not has_media and self._media_regex.search(message.content):
            has_media = True

        if has_media:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, don't try to sneak media in this channel!",
                delete_after=5,
            )
            return True

        return False


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FilterCog(bot), guilds=[Object(id=bot.guild_id)])
