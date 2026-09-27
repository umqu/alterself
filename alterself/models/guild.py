from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
from ..core.flake import Flake

if TYPE_CHECKING:
    from ..cache import StateCache
    from .member import Member
    from .channel import Channel


class Guild:
    __slots__ = (
        "_cache", "id", "name", "icon", "owner_id",
        "member_count", "description", "premium_tier",
        "premium_subscription_count", "_channels", "_members",
        "_unavailable",
    )

    def __init__(self, *, cache: "StateCache", data: dict) -> None:
        self._cache    = cache
        self._channels: Dict[Flake, "Channel"] = {}
        self._members:  Dict[Flake, "Member"]  = {}
        self._unavailable = False
        self._update(data)

    def _update(self, data: dict) -> None:
        self.id                       = Flake(data["id"])
        self.name                     = data.get("name", "")
        self.icon                     = data.get("icon")
        self.owner_id                 = Flake(data["owner_id"]) if data.get("owner_id") else None
        self.member_count             = data.get("member_count", 0)
        self.description              = data.get("description")
        self.premium_tier             = data.get("premium_tier", 0)
        self.premium_subscription_count = data.get("premium_subscription_count", 0)

    @property
    def channels(self) -> List["Channel"]:
        return list(self._channels.values())

    @property
    def members(self) -> List["Member"]:
        return list(self._members.values())

    @property
    def icon_url(self) -> Optional[str]:
        if not self.icon:
            return None
        ext = "gif" if self.icon.startswith("a_") else "png"
        return f"https://cdn.discordapp.com/icons/{self.id}/{self.icon}.{ext}?size=1024"

    def __repr__(self) -> str:
        return f"<Guild id={self.id} name={self.name!r}>"

    def __eq__(self, other) -> bool:
        return isinstance(other, Guild) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
