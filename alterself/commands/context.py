from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..client import Client
    from ..models.message import Message
    from ..models.user import User
    from ..models.guild import Guild
    from ..models.channel import Channel


class Context:

    __slots__ = (
        "client", "message", "command",
        "_prefix", "_args",
    )

    def __init__(
        self,
        *,
        client:  "Client",
        message: "Message",
        command=None,
        prefix:  str = "",
        args:    list | None = None,
    ) -> None:
        self.client  = client
        self.message = message
        self.command = command
        self._prefix = prefix
        self._args   = args or []

    @property
    def author(self) -> Optional["User"]:
        return self.message.author

    @property
    def channel(self) -> Optional["Channel"]:
        return self.message.channel

    @property
    def guild(self) -> Optional["Guild"]:
        return self.message.guild

    @property
    def channel_id(self) -> int:
        return int(self.message.channel_id)

    @property
    def guild_id(self) -> Optional[int]:
        return int(self.message.guild_id) if self.message.guild_id else None

    @property
    def args(self) -> list:
        return self._args

    async def send(self, content: str, **kwargs) -> "Message":
        data = await self.client.http.send_message(
            self.channel_id, content=content, **kwargs
        )
        from ..models.message import Message
        return Message(cache=self.client._cache, data=data)

    async def reply(self, content: str, **kwargs) -> "Message":
        kwargs.setdefault("message_reference", {
            "message_id": str(self.message.id),
            "channel_id": str(self.message.channel_id),
        })
        return await self.send(content, **kwargs)

    async def edit(self, content: str, **kwargs) -> "Message":
        data = await self.client.http.edit_message(
            self.channel_id, int(self.message.id), content=content, **kwargs
        )
        from ..models.message import Message
        return Message(cache=self.client._cache, data=data)

    async def delete(self) -> None:
        await self.client.http.delete_message(
            self.channel_id, int(self.message.id)
        )

    async def typing(self) -> None:
        await self.client.http.trigger_typing(self.channel_id)

    def __repr__(self) -> str:
        return f"<Context command={self.command!r} channel={self.channel_id}>"
