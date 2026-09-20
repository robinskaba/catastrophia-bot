import logging
import os
import aiohttp
from aiohttp.connector import ClientConnectorError
import discord
from discord.ext import commands
from discord import Intents

from src.common.config.config import Env

_FEATURES_PATH = "src/features"

_logger = logging.getLogger(__name__)


class CatastrophiaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=[], intents=Intents.all(), application_id=Env.APPLICATION_ID
        )

        self.session = None
        self.guild_id = Env.GUILD_ID

    def launch(self):
        token = Env.BOT_TOKEN

        try:
            self.run(token)
        except ClientConnectorError as e:
            _logger.error(f"failed to connect bot due to ClientConnectorError! {e}")

    async def setup_hook(self):
        # create aiohttp session
        self.session = aiohttp.ClientSession()

        for feature_folder in os.listdir(_FEATURES_PATH):
            feature_dir = os.path.join(_FEATURES_PATH, feature_folder)

            if os.path.isdir(feature_dir):
                for file in os.listdir(feature_dir):
                    if file.endswith("cog.py"):  # cog file detection
                        module_name = file[:-3]  # remove .py from end of file name

                        await self.load_extension(
                            f"{_FEATURES_PATH.replace("/", ".")}.{feature_folder}.{module_name}"
                        )

        await self.tree.sync(guild=discord.Object(id=self.guild_id))
        _logger.info("setup hook finished")

    async def on_ready(self):
        _logger.info(f"{self.user} bot is ready.")

    async def close(self):
        # close aiohttp session if exists
        if hasattr(self, "session") and self.session:
            await self.session.close()

        await super().close()
