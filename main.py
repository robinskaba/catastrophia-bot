import logging

from src.app.discord_bot import CatastrophiaBot

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} {levelname:<8} - {name}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    logger.info("CatastrophiaBot is booting up...")
    bot = CatastrophiaBot()
    bot.launch()
    logger.info("CatastrophiaBot is offline...")
