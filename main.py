import logging

from src.common.bot import CatastrophiaBot
from src.common.config.config import Env
from src.common.config.logging_filters import apply_logging_filters

_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG if Env.ENVIRONMENT == "DEV" else logging.INFO,
        format="{asctime} {levelname:<8} - {name}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    apply_logging_filters()

    _logger.info("CatastrophiaBot is booting up...")
    bot = CatastrophiaBot()
    bot.launch()
    _logger.info("CatastrophiaBot is offline...")
