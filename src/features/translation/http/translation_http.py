from enum import Enum

import aiohttp

from src.common.config.config import Env


class Language(Enum):
    ENGLISH = ("en",)
    RUSSIAN = "ru"


async def translate(message: str, source: Language, target: Language) -> str | None:
    async with aiohttp.ClientSession() as session:
        payload = {"q": message, "source": source.value, "target": target.value}
        async with session.post(
            f"{Env.TRANSLATION_ENDPOINT}/translate", json=payload
        ) as response:
            if response.status != 200:
                return None

            data = await response.json()
            translation = data.get("translatedText", "translation failed")
            return translation
