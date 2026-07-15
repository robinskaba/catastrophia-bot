from discord import Interaction, Message, Object, app_commands
from discord.ext import commands
from src.common.config.config import Env
from src.features.translation.http.translation_http import Language, translate


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

    async def translate_to_russian(self, interaction: Interaction, message: Message):
        await interaction.response.defer(ephemeral=True)
        russian_translation = await translate(
            message.content, Language.ENGLISH, Language.RUSSIAN
        )
        response = (
            russian_translation if russian_translation else "Перевод сейчас недоступен."
        )  # "Translation is unavailable right now."
        await interaction.followup.send(response)


async def setup(bot: commands.Bot):
    await bot.add_cog(TranslationCog(bot), guilds=[Object(id=bot.guild_id)])
