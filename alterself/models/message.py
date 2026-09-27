from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from datetime import datetime
from ..core.flake import Flake
from ..core.enums import MessageKind

if TYPE_CHECKING:
    from ..cache import StateCache


def _parse_ts(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


class Message:
    __slots__ = (
        "_cache", "id", "channel_id", "guild_id",
        "author", "content", "timestamp", "edited_timestamp",
        "tts", "mention_everyone", "mentions", "mention_roles",
        "attachments", "embeds", "reactions", "pinned",
        "kind", "flags", "sticker_items", "referenced_message",
        "interaction", "thread", "components",
    )

    def __init__(self, *, cache: "StateCache", data: dict) -> None:
        self._cache = cache
        self._update(data)

    def _update(self, data: dict) -> None:
        from .user import User
        self.id             = Flake(data["id"])
        self.channel_id     = Flake(data["channel_id"])
        self.guild_id       = Flake(data["guild_id"]) if data.get("guild_id") else None
        self.content        = data.get("content", "")
        self.timestamp      = _parse_ts(data.get("timestamp"))
        self.edited_timestamp = _parse_ts(data.get("edited_timestamp"))
        self.tts            = data.get("tts", False)
        self.mention_everyone = data.get("mention_everyone", False)
        self.pinned         = data.get("pinned", False)
        self.flags          = data.get("flags", 0)
        self.attachments    = data.get("attachments", [])
        self.embeds         = data.get("embeds", [])
        self.reactions      = data.get("reactions", [])
        self.sticker_items  = data.get("sticker_items", [])
        self.components     = data.get("components", [])
        self.interaction    = data.get("interaction")
        self.thread         = data.get("thread")

        try:
            self.kind = MessageKind(data.get("type", 0))
        except ValueError:
            self.kind = data.get("type", 0)

        author_data = data.get("author", {})
        self.author = User(cache=self._cache, data=author_data) if author_data else None

        self.mentions      = [User(cache=self._cache, data=u) for u in data.get("mentions", [])]
        self.mention_roles = data.get("mention_roles", [])

        ref = data.get("referenced_message")
        self.referenced_message = Message(cache=self._cache, data=ref) if ref else None

    @property
    def channel(self):
        return self._cache.get_channel(int(self.channel_id))

    @property
    def guild(self):
        return self._cache.get_guild(int(self.guild_id)) if self.guild_id else None

    @property
    def jump_url(self) -> str:
        gid = self.guild_id or "@me"
        return f"https://discord.com/channels/{gid}/{self.channel_id}/{self.id}"

    def __repr__(self) -> str:
        return f"<Message id={self.id} content={self.content[:50]!r}>"

    def __eq__(self, other) -> bool:
        return isinstance(other, Message) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
