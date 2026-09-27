from __future__ import annotations
import asyncio
from typing import Callable, List, Optional, Any


class Command:
    __slots__ = ("func", "name", "aliases", "checks", "brief")

    def __init__(
        self,
        func:    Callable,
        *,
        name:    Optional[str] = None,
        aliases: Optional[List[str]] = None,
        brief:   str = "",
    ) -> None:
        self.func    = func
        self.name    = name or func.__name__
        self.aliases = aliases or []
        self.checks: List[Callable] = []
        self.brief   = brief

    def add_check(self, check: Callable) -> None:
        self.checks.append(check)

    async def invoke(self, ctx, *args, **kwargs) -> Any:
        for check in self.checks:
            result = check(ctx)
            if asyncio.iscoroutine(result):
                result = await result
            if not result:
                from ..errors import CheckFailed
                raise CheckFailed(f"Check {check.__name__!r} failed")

        if asyncio.iscoroutinefunction(self.func):
            return await self.func(ctx, *args, **kwargs)
        return self.func(ctx, *args, **kwargs)

    def __repr__(self) -> str:
        return f"<Command {self.name!r}>"


def cmd(
    *,
    name:    Optional[str] = None,
    aliases: Optional[List[str]] = None,
    brief:   str = "",
) -> Callable:
    def decorator(func: Callable) -> Callable:
        command = Command(func, name=name, aliases=aliases, brief=brief)
        func._command = command
        return func
    return decorator
