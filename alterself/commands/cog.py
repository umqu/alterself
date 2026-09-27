from __future__ import annotations
import inspect
from typing import TYPE_CHECKING, List

from .core import Command

if TYPE_CHECKING:
    from ..client import Client


class Cog:

    @property
    def name(self) -> str:
        return type(self).__name__

    def _commands(self) -> List[Command]:
        cmds = []
        for _, val in inspect.getmembers(self):
            if hasattr(val, "_command"):
                cmds.append(val._command)
        return cmds

    def _inject(self, client: "Client") -> None:
        for cmd in self._commands():
                                                 
            original = cmd.func
            import functools

            @functools.wraps(original)
            async def bound(ctx, *args, _orig=original, _self=self, **kwargs):
                return await _orig(_self, ctx, *args, **kwargs)

            cmd.func = bound
            client.add_command(cmd)

    def cog_load(self) -> None:
        pass

    def cog_unload(self) -> None:
        pass
