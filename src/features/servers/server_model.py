from enum import Enum


class ServerStateMSG(Enum):
    OPEN = "Open"
    RECHARGING = "Recharging"
    MAINTANANCE = "Maintanance"
    TOURNAMENT = "Tournament"
    RESTART = "Restart"


class ServerStateMS(Enum):
    OPEN = None  # bez hodnoty znaci ze je open
    RECHARING = "R"
    MAINTANANCE = "M"
    TOURNAMENT = "T"
