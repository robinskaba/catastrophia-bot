import os
import discord
from discord.ext import commands
from discord import Intents

from src.config.config import Env

COGS_PATH = "src/app/cogs"


class CatastrophiaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=[], intents=Intents.all(), application_id=Env.APPLICATION_ID
        )

        self.guild_id = Env.GUILD_ID

    def launch(self):
        token = Env.BOT_TOKEN
        self.run(token)

    async def setup_hook(self):
        # load cogs
        for file in os.listdir(COGS_PATH):
            if not file.endswith(".py"):
                continue

            name = file[:-3]
            await self.load_extension(f"src.app.cogs.{name}")

        await self.tree.sync(guild=discord.Object(id=self.guild_id))
        print(f"Setup hook finished.")

    async def on_ready(self):
        print(f"{self.user} bot is ready.")
