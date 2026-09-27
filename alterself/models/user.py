from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from ..core.flake import Flake

if TYPE_CHECKING:
    from ..cache import StateCache


class User:
    __slots__ = (
        "_cache", "id", "username", "discriminator",
        "global_name", "avatar", "bot", "system",
        "public_flags", "premium_type",
    )

    def __init__(self, *, cache: "StateCache", data: dict) -> None:
        self._cache = cache
        self._update(data)

    def _update(self, data: dict) -> None:
        self.id             = Flake(data["id"])
        self.username       = data.get("username", "")
        self.discriminator  = data.get("discriminator", "0")
        self.global_name    = data.get("global_name")
        self.avatar         = data.get("avatar")
        self.bot            = data.get("bot", False)
        self.system         = data.get("system", False)
        self.public_flags   = data.get("public_flags", 0)
        self.premium_type   = data.get("premium_type", 0)

    @property
    def mention(self) -> str:
        return f"<@{self.id}>"

    @property
    def display_name(self) -> str:
        return self.global_name or self.username

    @property
    def avatar_url(self) -> Optional[str]:
        if not self.avatar:
            idx = (int(self.id) >> 22) % 6
            return f"https://cdn.discordapp.com/embed/avatars/{idx}.png"
        ext = "gif" if self.avatar.startswith("a_") else "png"
        return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.{ext}?size=1024"

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.username!r}>"

    def __eq__(self, other) -> bool:
        return isinstance(other, User) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
