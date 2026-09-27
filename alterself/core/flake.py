
from __future__ import annotations
import datetime

DISCORD_EPOCH = 1_420_070_400_000


class Flake(int):

    __slots__ = ()

    @property
    def timestamp_ms(self) -> int:
        return (self >> 22) + DISCORD_EPOCH

    @property
    def created_at(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self.timestamp_ms / 1000.0, tz=datetime.timezone.utc
        )

    @property
    def worker_id(self) -> int:
        return (self & 0x3E0000) >> 17

    @property
    def process_id(self) -> int:
        return (self & 0x1F000) >> 12

    @property
    def increment(self) -> int:
        return self & 0xFFF

    def __repr__(self) -> str:
        return f"Flake({int(self)}, created={self.created_at.isoformat()})"
