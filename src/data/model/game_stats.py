class GameStats:

    def __init__(self, playing: int, visits: int):
        self.playing = playing
        self.visits = visits

    @staticmethod
    def from_dict(data: dict) -> GameStats:
        return GameStats(playing=data.get("playing", -1), visits=data.get("visits", -1))
