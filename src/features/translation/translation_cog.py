import logging
import re

from discord import Interaction, Message, Object, TextChannel, app_commands
from discord.ext import commands
from src.common.config.config import Env
from src.features.translation.http.translation_http import Language, translate

_logger = logging.getLogger(__name__)


class TranslationCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._ctx_menu = app_commands.ContextMenu(
            name="Translate to Russian", callback=self.translate_to_russian
        )
        self._bot.tree.add_command(
            self._ctx_menu, guild=Object(id=Env.GUILD_ID)
        )  # specifying guild id maintains up-to-date slash and context commands

    async def cog_unload(self):
        self._bot.tree.remove_command(self._ctx_menu.name, type=self._ctx_menu.type)

    # context command for translating to russian
    async def translate_to_russian(self, interaction: Interaction, message: Message):
        await interaction.response.defer(ephemeral=False)
        russian_translation = await translate(
            message.content, Language.ENGLISH, Language.RUSSIAN
        )
        response = (
            russian_translation if russian_translation else "Перевод сейчас недоступен."
        )  # "Translation is unavailable right now."
        await interaction.followup.send(response)

    async def get_or_create_webhook(self, channel: TextChannel):
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.user == self._bot.user:
                return webhook
        return await channel.create_webhook(name="TranslationWebhook")

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # do not retrigger on bot messages or empty
        if message.author.bot or not message.content:
            return

        # regex search for basic cyrillic characters
        if not re.search(r"[А-Яа-яЁё]", message.content):
            return

        translation = await translate(
            message.content, Language.RUSSIAN, Language.ENGLISH
        )
        if not translation:
            _logger.warning(f"could not translate '{message.content}' to english")
            return

        # update message with translation
        webhook = await self.get_or_create_webhook(message.channel)
        msg_with_translation = f"{message.content} *({translation})*"
        await webhook.send(
            content=msg_with_translation,
            username=message.author.display_name,
            avatar_url=message.author.display_avatar.url,
        )
        await message.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(TranslationCog(bot), guilds=[Object(id=bot.guild_id)])
