import logging

_IGNORED_500_MESSAGES = [
    "WSServerHandshakeError: 520",
    "Temporary failure in name resolution",
]


class IgnoreDiscord500Filter(logging.Filter):
    def filter(self, record):
        for ignored_msg in _IGNORED_500_MESSAGES:
            if (ignored_msg in record.getMessage()) or (
                record.exc_info and ignored_msg in str(record.exc_info[1])
            ):
                return False
        return True


logging.getLogger("discord").addFilter(IgnoreDiscord500Filter())
logging.getLogger("discord.gateway").addFilter(IgnoreDiscord500Filter())
