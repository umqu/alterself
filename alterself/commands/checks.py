from __future__ import annotations
from ..errors import CheckFailed


def owner_only(ctx) -> bool:
    if not ctx.client.owner_ids:
        return ctx.author and str(ctx.author.id) == str(ctx.client._cache.me.id)
    return ctx.author and int(ctx.author.id) in ctx.client.owner_ids


def guild_only(ctx) -> bool:
    return ctx.guild_id is not None


def dm_only(ctx) -> bool:
    return ctx.guild_id is None


def check(predicate):
    def decorator(func):
        if hasattr(func, "_command"):
            func._command.add_check(predicate)
        else:
            if not hasattr(func, "_checks"):
                func._checks = []
            func._checks.append(predicate)
        return func
    return decorator
