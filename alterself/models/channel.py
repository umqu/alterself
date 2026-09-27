from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from ..core.flake import Flake
from ..core.enums import ChannelKind

if TYPE_CHECKING:
    from ..cache import StateCache
    from .user import User


class Channel:
    __slots__ = ("_cache", "id", "kind", "name", "guild_id",
                 "position", "topic", "nsfw", "parent_id", "last_message_id")

    def __init__(self, *, cache: "StateCache", data: dict) -> None:
        self._cache = cache
        self._update(data)

    def _update(self, data: dict) -> None:
        self.id             = Flake(data["id"])
        try:
            self.kind = ChannelKind(data.get("type", 0))
        except ValueError:
            self.kind = data.get("type", 0)
        self.name           = data.get("name")
        self.guild_id       = Flake(data["guild_id"]) if data.get("guild_id") else None
        self.position       = data.get("position", 0)
        self.topic          = data.get("topic")
        self.nsfw           = data.get("nsfw", False)
        self.parent_id      = Flake(data["parent_id"]) if data.get("parent_id") else None
        self.last_message_id= Flake(data["last_message_id"]) if data.get("last_message_id") else None

    @property
    def mention(self) -> str:
        return f"<#{self.id}>"

    def __repr__(self) -> str:
        return f"<Channel id={self.id} name={self.name!r} kind={self.kind}>"


class DMChannel(Channel):
    __slots__ = ("_recipient",)

    def __init__(self, *, cache: "StateCache", data: dict) -> None:
        self._recipient: Optional["User"] = None
        super().__init__(cache=cache, data=data)

    def _update(self, data: dict) -> None:
        super()._update(data)
        recipients = data.get("recipients", [])
        if recipients:
            from .user import User
            self._recipient = User(cache=self._cache, data=recipients[0])

    @property
    def recipient(self) -> Optional["User"]:
        return self._recipient


class GroupChannel(Channel):
    __slots__ = ("_recipients", "owner_id")

    def __init__(self, *, cache: "StateCache", data: dict) -> None:
        self._recipients: List["User"] = []
        self.owner_id: Optional[Flake] = None
        super().__init__(cache=cache, data=data)

    def _update(self, data: dict) -> None:
        super()._update(data)
        from .user import User
        self._recipients = [User(cache=self._cache, data=u) for u in data.get("recipients", [])]
        if data.get("owner_id"):
            self.owner_id = Flake(data["owner_id"])

    @property
    def recipients(self) -> List["User"]:
        return list(self._recipients)


def make_channel(cache: "StateCache", data: dict) -> Channel:
    kind = data.get("type", 0)
    if kind == ChannelKind.DM:
        return DMChannel(cache=cache, data=data)
    if kind == ChannelKind.GROUP_DM:
        return GroupChannel(cache=cache, data=data)
    return Channel(cache=cache, data=data)
