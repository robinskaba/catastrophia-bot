from datetime import timedelta, timezone
import logging
import re
from discord import Message, Object, datetime
from discord.ext import commands, tasks

from src.config.config import Config, Env

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

logger = logging.getLogger(__name__)


class FilterCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self._youtube_regex = re.compile(
            r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+"
        )
        self._media_regex = re.compile(
            r"\.(gif|png|jpe?g|webp|bmp|mp4|webm|mov)|tenor\.com/view|giphy\.com/media|imgur\.com|youtube\.com|youtu\.be",
            re.IGNORECASE,
        )

    async def cog_load(self):
        self.check_inactive_creators.start()

    async def cog_unload(self):
        self.check_inactive_creators.cancel()

    @tasks.loop(hours=24)
    async def check_inactive_creators(self):
        await self.bot.wait_until_ready()

        guild = self.bot.get_guild(Env.GUILD_ID)
        if not guild:
            return

        channel = self.bot.get_channel(Config.YOUTUBE_VIDEOS_CHANNEL_ID)
        role = guild.get_role(Config.CONTENT_CREATOR_ROLE_ID)

        if not channel or not role:
            return

        three_months_ago = datetime.now(timezone.utc) - timedelta(
            days=Config.CONTENT_CREATOR_INACTIVITY_MAX
        )
        active_members = set()

        async for msg in channel.history(limit=None, after=three_months_ago):
            if self._youtube_regex.search(msg.content):
                active_members.add(msg.author.id)

        for member in role.members:
            if member.id not in active_members:
                logger.info(
                    f"member {member.name} lost his content creator status due to not posting for {Config.CONTENT_CREATOR_INACTIVITY_MAX} days."
                )
                await member.remove_roles(role)

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

    async def enforce_youtube_videos(self, message: Message):
        """Delete messages in #youtube-videos if they are not a youtube link."""

        if not self._youtube_regex.search(message.content):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, this channel is for **youtube videos only!**",
                delete_after=10,
            )
            logger.info(
                f"removed non-youtube link message from @{message.author.name}: '{message.content}'"
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
            logger.info(
                f"removed sneaky media in #{message.channel.name} from @{message.author.name}"
            )
            return True

        return False


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FilterCog(bot), guilds=[Object(id=bot.guild_id)])
