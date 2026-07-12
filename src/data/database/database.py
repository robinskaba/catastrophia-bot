import logging
import sqlite3

_DATABASE_PATH = "catastrophia-bot.db"
_SCHEMA_PATH = "src/data/database/schema.sql"

_logger = logging.getLogger(__name__)


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "conn"):
            self.conn = sqlite3.connect(_DATABASE_PATH)
            self.cursor = self.conn.cursor()
            self.setup()

    def setup(self):
        with open(_SCHEMA_PATH, "r") as r:
            schema = r.read()
        self.cursor.executescript(schema)
        self.conn.commit()

    def close(self):
        self.conn.close()
        _logger.info("database disconnected")
