from datetime import datetime, timedelta


class Restriction:
    def __init__(self, time: datetime, duration: int, active: bool, reason: str):
        self.time = time
        self.duration = duration
        self.active = active
        self.reason = reason

    def get_end(self) -> datetime | None:
        if not self.duration:
            return None
        return self.time + timedelta(seconds=self.duration)

    @property
    def is_ongoing(self) -> bool:
        if not self.active:
            return False
        if not self.duration:
            return True

        return datetime.now(self.time.tzinfo) < self.get_end()
