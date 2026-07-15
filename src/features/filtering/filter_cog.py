from datetime import timedelta, timezone
import logging
import re
from discord import Message, Object, datetime
from discord.ext import commands, tasks
from src.common.config.config import Config, Env
from src.features.filtering.services.creator_service import CreatorService

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

_logger = logging.getLogger(__name__)


class FilterCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._creator_service = CreatorService()
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
        await self._bot.wait_until_ready()

        guild = self._bot.get_guild(Env.GUILD_ID)
        if not guild:
            _logger.warning("no guild")
            return

        channel = self._bot.get_channel(Config.YOUTUBE_VIDEOS_CHANNEL_ID)
        role = guild.get_role(Config.CONTENT_CREATOR_ROLE_ID)

        if not channel or not role:
            _logger.warning("missing youtube channel or content creator role")
            return

        now_utc = datetime.now(timezone.utc)
        max_inactivity_ago = now_utc - timedelta(
            days=Config.CONTENT_CREATOR_INACTIVITY_MAX
        )
        active_members = set()

        async for msg in channel.history(limit=None, after=max_inactivity_ago):
            if self._youtube_regex.search(msg.content):
                active_members.add(msg.author.id)

        for member in role.members:
            creator = self._creator_service.get_or_create(member.id)
            role_given = datetime.fromtimestamp(creator.since, tz=timezone.utc)
            if now_utc - role_given < timedelta(
                days=Config.CONTENT_CREATOR_INACTIVITY_MAX
            ):
                continue  # creator is safe, because he received the role in the last 'CONTENT_CREATOR_INACTIVITY_MAX' days

            if member.id not in active_members:
                _logger.info(
                    f"member {member.name} lost his content creator status due to not posting for {Config.CONTENT_CREATOR_INACTIVITY_MAX} days."
                )
                await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:  # to prevent infinite loop
            return

        # owner can bypass filters
        if message.author.get_role(Config.OWNER_ROLE_ID):
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
            _logger.info(
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
            _logger.info(
                f"removed sneaky media in #{message.channel.name} from @{message.author.name}"
            )
            return True

        return False


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FilterCog(bot), guilds=[Object(id=bot.guild_id)])
