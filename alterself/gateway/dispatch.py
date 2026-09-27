
from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..cache import StateCache

log = logging.getLogger(__name__)

                                                                            
                                                                        
_HANDLER_PARAM_CACHE: Dict[int, bool] = {}


def _handler_wants_arg(handler: Callable) -> bool:
    hid = id(handler)
    if hid not in _HANDLER_PARAM_CACHE:
        try:
            sig = inspect.signature(handler)
            positional = [
                p for p in sig.parameters.values()
                if p.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.VAR_POSITIONAL,
                )
            ]
            _HANDLER_PARAM_CACHE[hid] = len(positional) > 0
        except (ValueError, TypeError):
            _HANDLER_PARAM_CACHE[hid] = True                          
    return _HANDLER_PARAM_CACHE[hid]


class EventBus:

    def __init__(self, cache: "StateCache") -> None:
        self._cache    = cache
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._parsers   = self._wire_parsers()

                                                                          
                  
                                                                          

    def on(self, event: str, handler: Callable) -> None:
        key = event.upper()
        self._handlers[key].append(handler)
                                                                           
        _handler_wants_arg(handler)

    def off(self, event: str, handler: Callable) -> None:
        key = event.upper()
        lst = self._handlers.get(key, [])
        try:
            lst.remove(handler)
        except ValueError:
            pass
                                        
        _HANDLER_PARAM_CACHE.pop(id(handler), None)

                                                                          
          
                                                                          

    async def emit(self, event: str, data: Any) -> None:
        event = event.upper()

                                                                                  
        parser = self._parsers.get(event)
        result = data
        if parser:
            try:
                parsed = parser(data)
                                                                               
                if parsed is not None:
                    result = parsed
            except Exception as exc:
                log.exception("Cache parser error for %s: %s", event, exc)

                                                                
        handler_name = "unknown"
        for handler in self._handlers.get(event, []):
            try:
                handler_name = getattr(handler, "__name__", repr(handler))
                wants_arg    = _handler_wants_arg(handler)
                call_args    = (result,) if wants_arg else ()

                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(
                        handler(*call_args),
                        name=f"alterself:event:{event}:{handler_name}",
                    )
                else:
                    handler(*call_args)
            except Exception as exc:
                log.exception(
                    "Handler error in %s for event %s: %s",
                    handler_name, event, exc,
                )

                                                                          
                   
                                                                          

    def _wire_parsers(self) -> Dict[str, Callable]:
        c = self._cache
        return {
            "READY":                          c.parse_ready,
            "RESUMED":                        c.parse_resumed,
            "USER_UPDATE":                    c.parse_user_update,
            "GUILD_CREATE":                   c.parse_guild_create,
            "GUILD_UPDATE":                   c.parse_guild_update,
            "GUILD_DELETE":                   c.parse_guild_delete,
            "GUILD_MEMBER_ADD":               c.parse_guild_member_add,
            "GUILD_MEMBER_REMOVE":            c.parse_guild_member_remove,
            "GUILD_MEMBER_UPDATE":            c.parse_guild_member_update,
            "CHANNEL_CREATE":                 c.parse_channel_create,
            "CHANNEL_UPDATE":                 c.parse_channel_update,
            "CHANNEL_DELETE":                 c.parse_channel_delete,
            "CHANNEL_RECIPIENT_ADD":          c.parse_channel_recipient_add,
            "CHANNEL_RECIPIENT_REMOVE":       c.parse_channel_recipient_remove,
            "THREAD_CREATE":                  c.parse_thread_create,
            "THREAD_UPDATE":                  c.parse_thread_update,
            "THREAD_DELETE":                  c.parse_thread_delete,
            "MESSAGE_CREATE":                 c.parse_message_create,
            "MESSAGE_UPDATE":                 c.parse_message_update,
            "MESSAGE_DELETE":                 c.parse_message_delete,
            "MESSAGE_DELETE_BULK":            c.parse_message_delete_bulk,
            "MESSAGE_REACTION_ADD":           c.parse_reaction_add,
            "MESSAGE_REACTION_REMOVE":        c.parse_reaction_remove,
            "MESSAGE_REACTION_REMOVE_ALL":    c.parse_message_reaction_remove_all,
            "MESSAGE_REACTION_REMOVE_EMOJI":  c.parse_message_reaction_remove_emoji,
            "TYPING_START":                   c.parse_typing_start,
            "PRESENCE_UPDATE":                c.parse_presence_update,
            "RELATIONSHIP_ADD":               c.parse_relationship_add,
            "RELATIONSHIP_REMOVE":            c.parse_relationship_remove,
            "VOICE_STATE_UPDATE":             c.parse_voice_state_update,
            "VOICE_SERVER_UPDATE":            c.parse_voice_server_update,
            "GUILD_MEMBERS_CHUNK":            c.parse_guild_members_chunk,
            "THREAD_LIST_SYNC":               c.parse_thread_list_sync,
            "CALL_CREATE":                    c.parse_call_create,
            "CALL_UPDATE":                    c.parse_call_update,
            "CALL_DELETE":                    c.parse_call_delete,
        }
