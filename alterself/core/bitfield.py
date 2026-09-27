
from __future__ import annotations
from typing import Iterator


class Bitfield:

    VALID_FLAGS: dict[str, int] = {}

    def __init__(self, value: int = 0):
        self.value = value

    def __contains__(self, flag: str) -> bool:
        bit = self.VALID_FLAGS.get(flag, 0)
        return bool(self.value & bit)

    def __iter__(self) -> Iterator[str]:
        for name, bit in self.VALID_FLAGS.items():
            if self.value & bit:
                yield name

    def __repr__(self) -> str:
        active = list(self)
        return f"{self.__class__.__name__}({self.value}, flags={active})"

    def has(self, *flags: str) -> bool:
        return all(f in self for f in flags)

    def add(self, *flags: str) -> "Bitfield":
        for f in flags:
            self.value |= self.VALID_FLAGS[f]
        return self

    def remove(self, *flags: str) -> "Bitfield":
        for f in flags:
            self.value &= ~self.VALID_FLAGS[f]
        return self
