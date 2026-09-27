
from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .spoof   import SpoofEngine
from .http    import HTTPLayer
from .gateway import GatewaySocket, EventBus
from .cache   import StateCache
from .commands.core    import Command, cmd
from .commands.cog     import Cog
from .commands.context import Context
from .errors  import CommandError, CheckFailed
from .models.message import Message

log = logging.getLogger(__name__)


class Client:

    def __init__(
        self,
        *,
        token:     str,
        prefix:    Union[str, Callable] = "!",
        owner_ids: Optional[List[int]]  = None,
        proxy:     Optional[str]        = None,
        pacing:    bool                 = True,
    ) -> None:
        self.token     = token
        self.prefix    = prefix
        self.owner_ids: Set[int] = set(owner_ids) if owner_ids else set()

                                                                        
                                                                           
                                      
        self._spoof  = SpoofEngine(token)
        self.http    = HTTPLayer(token, self._spoof, proxy=proxy, pacing=pacing)
        self._cache  = StateCache(self.http)
        self._bus    = EventBus(self._cache)
        self._gw     = GatewaySocket(self._bus, token, self._spoof)

                          
        self._commands: Dict[str, Command] = {}
        self._cogs:     Dict[str, Cog]     = {}
                                                                
        self._cog_commands: Dict[str, List[str]] = {}

                                                                        
        self._ready:  Optional[asyncio.Event] = None
        self._closed  = False

                                      
        self._bus.on("READY",          self._handle_ready)
        self._bus.on("MESSAGE_CREATE", self._handle_message)

                                                                          
                
                                                                          

    @property
    def me(self):
        return self._cache.me

    @property
    def guilds(self):
        return self._cache.guilds

    @property
    def latency(self) -> float:
        return self._gw.latency

    @property
    def commands(self) -> List[Command]:
                             
        return list({id(c): c for c in self._commands.values()}.values())

    @property
    def cogs(self) -> List[Cog]:
        return list(self._cogs.values())

                                                                          
                        
                                                                          

    def on_event(self, coro: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError(f"Event handler {coro.__name__!r} must be async")
        name = coro.__name__
        event = (name[3:] if name.startswith("on_") else name).upper()
        self._bus.on(event, coro)
        return coro

    def listen(self, event: str) -> Callable:
        def decorator(coro: Callable) -> Callable:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError(f"Listener {coro.__name__!r} must be async")
            self._bus.on(event.upper(), coro)
            return coro
        return decorator

    def add_listener(self, event: str, handler: Callable) -> None:
        self._bus.on(event.upper(), handler)

    def remove_listener(self, event: str, handler: Callable) -> None:
        self._bus.off(event.upper(), handler)

                                                                          
              
                                                                          

    def command(
        self,
        *,
        name:    Optional[str]       = None,
        aliases: Optional[List[str]] = None,
        brief:   str                 = "",
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            c = Command(func, name=name, aliases=aliases, brief=brief)
            self.add_command(c)
            func._command = c
            return func
        return decorator

    def add_command(self, c: Command) -> None:
                                                              
        name = c.name.lower()
        aliases = [a.lower() for a in c.aliases]
        c.name    = name
        c.aliases = aliases

                                                                
        conflicts = []
        if name in self._commands:
            conflicts.append(name)
        for a in aliases:
            if a in self._commands:
                conflicts.append(a)
        if conflicts:
            raise ValueError(f"Command name/alias already registered: {conflicts}")

        self._commands[name] = c
        for a in aliases:
            self._commands[a] = c

    def remove_command(self, name: str) -> Optional[Command]:
        name = name.lower()
        c = self._commands.pop(name, None)
        if c:
            for a in c.aliases:
                self._commands.pop(a.lower(), None)
        return c

    def get_command(self, name: str) -> Optional[Command]:
        return self._commands.get(name.lower())

    def add_cog(self, cog: Cog) -> None:
        if cog.name in self._cogs:
            raise ValueError(f"Cog {cog.name!r} already loaded")
        cog._inject(self)
        registered = [c.name for c in cog._commands()]
        self._cog_commands[cog.name] = registered
        self._cogs[cog.name]         = cog
        cog.cog_load()
        log.info("Cog loaded: %s (%d commands)", cog.name, len(registered))

    def remove_cog(self, name: str) -> None:
        cog = self._cogs.pop(name, None)
        if not cog:
            return
                                                   
        for cmd_name in self._cog_commands.pop(name, []):
            self._commands.pop(cmd_name, None)
                                 
            for a in list(self._commands.keys()):
                if self._commands.get(a) and self._commands[a].name == cmd_name:
                    del self._commands[a]
        cog.cog_unload()
        log.info("Cog unloaded: %s", name)

                                                                          
                     
                                                                          

    def run(self, *, log_level: int = logging.INFO) -> None:
        logging.basicConfig(
            level  = log_level,
            format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt= "%H:%M:%S",
        )

        async def _runner():
            try:
                await self.start()
            finally:
                await self.close()

        try:
            asyncio.run(_runner())
        except KeyboardInterrupt:
            pass

    async def start(self) -> None:
                                                               
        self._ready = asyncio.Event()
        await self._gw.connect()

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._gw.close()
        await self.http.close()
        log.info("Client closed cleanly")

    async def wait_until_ready(self, timeout: float = 30.0) -> None:
        if self._ready is None:
            self._ready = asyncio.Event()
        await asyncio.wait_for(self._ready.wait(), timeout)

                                                                          
              
                                                                          

    async def change_presence(
        self,
        *,
        status:     str        = "online",
        activities: list | None = None,
        afk:        bool       = False,
    ) -> None:
        from .activity import Activity
        raw = []
        for a in (activities or []):
            raw.append(a.to_dict() if isinstance(a, Activity) else a)
        await self._gw.send_presence(status=status, activities=raw, afk=afk)

                                                                          
                       
                                                                          

    async def _handle_ready(self, user) -> None:
        if self.me:
            self.owner_ids.add(int(self.me.id))
        if self._ready:
            self._ready.set()
        log.info("alterself ready — %s (%s)", self.me, self.me.id if self.me else "?")

    async def _handle_message(self, message: Any) -> None:
        if not isinstance(message, Message):
            return

                                                                
        if self.me is None:
            return

                                            
        if not message.author or message.author.id != self.me.id:
            return

        content = message.content or ""

                        
        prefix = self.prefix
        if callable(prefix):
            try:
                if asyncio.iscoroutinefunction(prefix):
                    prefix = await prefix(self, message)
                else:
                    prefix = prefix(self, message)
            except Exception as exc:
                log.warning("Prefix resolver raised: %s", exc)
                return

        if not isinstance(prefix, str) or not content.startswith(prefix):
            return

        rest  = content[len(prefix):]
        parts = rest.split()
        if not parts:
            return

                                                                       
        cmd_name = parts[0].lower()
        c = self._commands.get(cmd_name)
        if c is None:
            return

        args = parts[1:]
        ctx  = Context(
            client  = self,
            message = message,
            command = c,
            prefix  = prefix,
            args    = args,
        )

        try:
            await c.invoke(ctx, *args)
        except CheckFailed as exc:
            log.debug("Check failed [%s]: %s", c.name, exc)
        except CommandError as exc:
            log.warning("Command error [%s]: %s", c.name, exc)
        except Exception as exc:
            log.exception("Unhandled exception in command [%s]: %s", c.name, exc)
