import json
import logging
import os
import aiohttp
from aiohttp.connector import ClientConnectorError
import asyncpg
import discord
from discord.ext import commands
from discord import Intents, Interaction, Member, TextChannel

from src.common.config.config import Env
from src.common.db.command_usage import add_command_usage

_FEATURES_PATH = "src/features"
_SCHEMA_PATH = "sql/schema.sql"

_logger = logging.getLogger(__name__)


class CatastrophiaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=[], intents=Intents.all(), application_id=Env.APPLICATION_ID
        )

        self.guild_id = Env.GUILD_ID

        self.session = None
        self.pool = None

    def launch(self):
        token = Env.BOT_TOKEN

        try:
            self.run(token)
        except ClientConnectorError as e:
            _logger.error(f"failed to connect bot due to ClientConnectorError! {e}")

    async def setup_hook(self):
        # create aiohttp session
        self.session = aiohttp.ClientSession()

        # connect to database
        dsn = f"postgres://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('POSTGRES_DB')}"
        self.pool = await asyncpg.create_pool(dsn=dsn)
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()
        await self.pool.execute(schema)

        # load cogs
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

        # close database connection
        if self.pool:
            await self.pool.close()

        await super().close()

    async def on_app_command_completion(self, interaction: Interaction, command):
        # record command usage

        user = interaction.user
        command_name = command.name
        arguments = vars(interaction.namespace)

        async with self.pool.acquire() as conn:
            await add_command_usage(
                conn=conn,
                command_name=command_name,
                discord_id=user.id,
                arguments=json.dumps(
                    arguments,
                    skipkeys=True,  # skip unknown types
                    default=lambda a: a.id,  # member -> member.id, channel -> channel.id
                ),
            )
