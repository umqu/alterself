from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime, timezone
from ..core.flake import Flake

if TYPE_CHECKING:
    from ..cache import StateCache


class Member:
    __slots__ = ("_cache", "id", "guild_id", "_user_data",
                 "nick", "roles", "joined_at", "premium_since",
                 "deaf", "mute", "pending", "flags")

    def __init__(self, *, cache: "StateCache", data: dict) -> None:
        self._cache = cache
        self._update(data)

    def _update(self, data: dict) -> None:
        user_data = data.get("user", {})
        self.id       = Flake(user_data.get("id", 0))
        self.guild_id = Flake(data["guild_id"]) if data.get("guild_id") else None
        self._user_data = user_data
        self.nick     = data.get("nick")
        self.roles    = [Flake(r) for r in data.get("roles", [])]
        self.joined_at= data.get("joined_at")
        self.premium_since = data.get("premium_since")
        self.deaf     = data.get("deaf", False)
        self.mute     = data.get("mute", False)
        self.pending  = data.get("pending", False)
        self.flags    = data.get("flags", 0)

    @property
    def user(self):
        return self._cache.get_user(int(self.id)) if self.id else None

    @property
    def display_name(self) -> str:
        u = self.user
        return self.nick or (u.display_name if u else str(self.id))

    def __repr__(self) -> str:
        return f"<Member id={self.id} nick={self.nick!r}>"
