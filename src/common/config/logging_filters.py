import logging


class DiscordReconnectNoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not record.exc_info:
            return True

        exc_type, exc_value, _ = record.exc_info
        if exc_type is None:
            return True

        exc_name = exc_type.__name__
        exc_str = str(exc_value)

        if exc_name == "WSServerHandshakeError" and "520" in exc_str:
            return False

        if (
            exc_name == "ClientConnectorDNSError"
            or "Temporary failure in name resolution" in exc_str
        ):
            record.msg = "Disconnected from the internet, attempting to reconnect..."
            record.args = ()
            record.levelno = logging.WARNING
            record.levelname = "WARNING"
            record.exc_info = None
            record.exc_text = None
            return True

        return True


def apply_logging_filters():
    noise_filter = DiscordReconnectNoiseFilter()
    logging.getLogger("discord.client").addFilter(noise_filter)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
