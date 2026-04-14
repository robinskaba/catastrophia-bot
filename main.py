import logging

from src.app.discord_bot import CatastrophiaBot

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} {levelname:<8} - {name}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    print("CatastrophiaBot is booting up...")
    bot = CatastrophiaBot()
    bot.launch()
    print("---------------------------------- powered down...")
