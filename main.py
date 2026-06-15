import logging

from src.app.discord_bot import CatastrophiaBot
from src.config.logging_filters import apply_logging_filters

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} {levelname:<8} - {name}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )
    apply_logging_filters()

    logger.info("CatastrophiaBot is booting up...")
    bot = CatastrophiaBot()
    bot.launch()
    logger.info("CatastrophiaBot is offline...")
