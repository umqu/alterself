
from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import time
import zlib
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Set

import websockets

from ..errors import GatewayError, SessionClosed
from .heartbeat import HeartbeatManager

if TYPE_CHECKING:
    from .dispatch import EventBus
    from ..spoof import SpoofEngine

log = logging.getLogger(__name__)

GATEWAY_URL = "wss://gateway.discord.gg/?encoding=json&v=9&compress=zlib-stream"
ZLIB_SUFFIX = b"\x00\x00\xff\xff"

                                                           
import websockets.version as _wv
_WS_MAJOR = int(_wv.version.split(".")[0])
_WS_HEADER_KW = "extra_headers" if _WS_MAJOR >= 12 else "additional_headers"


class _State(Enum):
    IDLE       = "idle"
    CONNECTING = "connecting"
    OPEN       = "open"
    RESUMING   = "resuming"
    CLOSING    = "closing"
    DEAD       = "dead"


RESUMABLE = {4000, 4001, 4002, 4003, 4005, 4006, 4007, 4008, 4009}
FATAL     = {4004, 4010, 4011, 4012, 4013, 4014, 4015, 4016}


class GatewaySocket:

    __slots__ = (
        "_bus", "_token", "_spoof",
        "_ws", "_state", "_seq", "_session_id",
        "_resume_url", "_hb",
        "_buf", "_inflator",
        "_closed_ev", "_ready_ev",
        "_reconnect_attempts", "_max_attempts",
        "_base_delay", "_subscribed_guilds",
        "_connect_ts", "_identify_sent",
    )

    def __init__(
        self,
        bus:          "EventBus",
        token:        str,
        spoof:        "SpoofEngine",
        max_attempts: int   = 10,
        base_delay:   float = 1.0,
    ) -> None:
        self._bus     = bus
        self._token   = token
        self._spoof   = spoof
        self._ws      = None
        self._state   = _State.IDLE
        self._seq:    Optional[int] = None
        self._session_id:  Optional[str] = None
        self._resume_url:  Optional[str] = None
        self._hb:     Optional[HeartbeatManager] = None
        self._buf     = bytearray()
        self._inflator = zlib.decompressobj()
                                                                        
                                                               
        self._closed_ev  = asyncio.Event()
        self._ready_ev   = asyncio.Event()
        self._reconnect_attempts = 0
        self._max_attempts       = max_attempts
        self._base_delay         = base_delay
        self._subscribed_guilds: Set[int] = set()
        self._connect_ts: int = 0
        self._identify_sent: bool = False

                                                                          
            
                                                                          

    @property
    def latency(self) -> float:
        return self._hb.latency if self._hb else 0.0

    @property
    def connected(self) -> bool:
        return self._state in (_State.OPEN, _State.RESUMING)

    @property
    def closed(self) -> bool:
        return self._state == _State.DEAD

    async def connect(self) -> None:
        self._closed_ev.clear()
        self._ready_ev.clear()
        self._state = _State.CONNECTING
        self._reconnect_attempts = 0
        await self._connect_loop()

    async def close(self, code: int = 1000) -> None:
        if self._state == _State.DEAD:
            return
        self._state = _State.CLOSING
        self._closed_ev.set()
        if self._hb:
            self._hb.stop()
            self._hb = None
        if self._ws:
            try:
                                                                                  
                await self._ws.close(code, None)
            except Exception:
                pass
            self._ws = None
        self._state = _State.DEAD
        self._ready_ev.clear()
        log.info("Gateway closed (code=%d)", code)

    async def wait_ready(self, timeout: float = 30.0) -> None:
        await asyncio.wait_for(self._ready_ev.wait(), timeout)

    async def send_json(self, data: dict) -> None:
        if not self._ws:
            return
        try:
            await self._ws.send(json.dumps(data))
        except Exception as exc:
                                                              
            log.warning("send_json failed: %s", exc)
            raise ConnectionResetError(f"WebSocket send failed: {exc}") from exc

                                                                          
                       
                                                                          

    async def send_presence(
        self,
        status:     str  = "online",
        activities: list | None = None,
        afk:        bool = False,
        since:      int  = 0,
    ) -> None:
        await self.send_json({
            "op": 3,
            "d": {
                "status":     status,
                "since":      since,
                "activities": activities or [],
                "afk":        afk,
            },
        })

    async def send_voice_state(
        self,
        guild_id:   Optional[int],
        channel_id: Optional[int],
        self_mute:  bool = False,
        self_deaf:  bool = False,
        self_video: bool = False,
        flags:      int  = 0,
    ) -> None:
        await self.send_json({
            "op": 4,
            "d": {
                "guild_id":   str(guild_id)   if guild_id   is not None else None,
                "channel_id": str(channel_id) if channel_id is not None else None,
                "self_mute":  self_mute,
                "self_deaf":  self_deaf,
                "self_video": self_video,
                "flags":      flags,
            },
        })

    async def request_call_connect(self, channel_id: int) -> None:
        await self.send_json({"op": 13, "d": {"channel_id": str(channel_id)}})

                                                                          
                  
                                                                          

    async def _connect_loop(self) -> None:
        while self._reconnect_attempts < self._max_attempts:
            try:
                await self._do_connect()
                                                               
                self._reconnect_attempts = 0
                return
            except SessionClosed as exc:
                if exc.code in FATAL:
                    log.critical("Fatal gateway close %d — stopping", exc.code)
                    self._state = _State.DEAD
                    self._reconnect_attempts = 0                               
                    raise
                self._reconnect_attempts += 1
                wait = self._backoff()
                log.warning(
                    "Gateway closed (code=%s) — reconnect #%d in %.2f s",
                    exc.code, self._reconnect_attempts, wait,
                )
                await asyncio.sleep(wait)
            except Exception as exc:
                self._reconnect_attempts += 1
                wait = self._backoff()
                log.warning(
                    "Connection error: %s — retry #%d in %.2f s",
                    exc, self._reconnect_attempts, wait,
                )
                await asyncio.sleep(wait)

        self._state = _State.DEAD
        raise GatewayError(f"Max reconnect attempts ({self._max_attempts}) exceeded")

    def _backoff(self) -> float:
        delay = min(self._base_delay * (2 ** self._reconnect_attempts), 60.0)
        return delay + random.uniform(0.0, delay * 0.1)

    async def _do_connect(self) -> None:
        url = self._resume_url or GATEWAY_URL
        self._buf      = bytearray()
        self._inflator = zlib.decompressobj()
        self._identify_sent = False
        self._connect_ts    = math.floor(time.time() * 1000)

        connect_kwargs = {
            _WS_HEADER_KW: self._spoof.get_ws_headers(),
            "max_size": 2 ** 26,
            "open_timeout": 20,
        }

        self._ws = await websockets.connect(url, **connect_kwargs)
                                                                         
                                                                        
        log.info("WebSocket connected → %s", url)

        try:
            await self._message_loop()
        except websockets.exceptions.ConnectionClosed as exc:
            self._state = _State.IDLE
            raise SessionClosed(code=exc.code) from exc
        except ConnectionResetError as exc:
                              
            self._state      = _State.IDLE
            self._session_id = None
            self._seq        = None
            raise GatewayError(str(exc)) from exc

                                                                          
                  
                                                                          

    async def _message_loop(self) -> None:
        async for raw in self._ws:
            await self._ingest(raw)

    async def _ingest(self, raw) -> None:
        if isinstance(raw, bytes):
            self._buf.extend(raw)
            if len(raw) < 4 or raw[-4:] != ZLIB_SUFFIX:
                return
            try:
                decoded   = self._inflator.decompress(self._buf)
                self._buf = bytearray()
                raw       = decoded.decode("utf-8")
            except zlib.error as exc:
                log.error("zlib decompress error: %s — resetting inflator", exc)
                self._buf      = bytearray()
                self._inflator = zlib.decompressobj()
                return

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            log.error("JSON parse error: %s", exc)
            return

        await self._dispatch_op(payload)

                                                                          
                 
                                                                          

    async def _dispatch_op(self, p: dict) -> None:
        op    = p.get("op")
        data  = p.get("d")
        seq   = p.get("s")
        event = p.get("t")

        if seq is not None:
            self._seq = seq

                                                                        
        if op == 10:
            self._state = _State.OPEN                                            
            interval = data["heartbeat_interval"]
            if self._hb:
                self._hb.stop()
            self._hb = HeartbeatManager(self, interval, lambda: self._seq)
            self._hb.start()
            if self._session_id and self._seq is not None:
                                                                                  
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await self._resume()
            else:
                await self._identify()

                                                                        
        elif op == 11:
            if self._hb:
                self._hb.ack()

                                                                        
        elif op == 1:
            await self.send_json({"op": 1, "d": self._seq})

                                                                        
        elif op == 9:
                                                                      
            wait = random.uniform(1.0, 5.0)
            await asyncio.sleep(wait)
            if data is True:
                log.info("Invalid session — resumable, attempting RESUME")
                await self._resume()
            else:
                log.warning("Invalid session — re-identifying")
                self._session_id = None
                self._seq        = None
                await self._identify()

                                                                        
        elif op == 7:
            log.info("Gateway requested reconnect (op 7)")
            await self.close(4000)
            raise SessionClosed(code=4000)

                                                                        
        elif op == 0:
            if event == "READY":
                self._session_id  = data["session_id"]
                self._resume_url  = data.get("resume_gateway_url")
                self._identify_sent = True
                self._spoof.rotate_session()
                                                                 
                self._ready_ev.set()
                log.info("READY — session_id=%s", self._session_id)
                asyncio.create_task(
                    self._post_ready(data),
                    name="alterself:post_ready",
                )

            elif event == "RESUMED":
                self._state = _State.OPEN
                self._ready_ev.set()
                log.info("RESUMED")

            await self._bus.emit(event, data)

                                                                        
        elif op in (40, 41):
            log.debug("Gateway op %d (internal)", op)

        else:
            log.debug("Unknown gateway op %d", op)

                                                                          
                       
                                                                          

    async def _identify(self) -> None:
        capabilities = (
            (1 << 0)  |                    
            (1 << 1)  |                       
            (1 << 2)  |                          
            (1 << 3)  |                                  
            (1 << 4)  |                        
            (1 << 5)  |                              
            (1 << 6)  |                                          
            (1 << 7)  |                            
            (1 << 8)  |                       
            (1 << 9)  |                        
            (1 << 10) |                    
            (1 << 11) |                         
            (1 << 17) |                      
            (1 << 18)                                                      
        )

        await self.send_json({
            "op": 2,
            "d": {
                "token":        self._token,
                "capabilities": capabilities,
                "properties":   self._spoof.get_identify_props(),
                "presence": {
                    "status":     "unknown",
                    "since":      0,
                    "activities": [],
                    "afk":        False,
                },
                "compress":     False,
                "client_state": {
                    "guild_versions":          {},
                    "highest_last_message_id": "0",
                    "read_state_version":      0,
                    "user_guild_settings_version": -1,
                    "private_channels_version": "0",
                    "api_code_version":         0,
                },
            },
        })
        log.info("IDENTIFY sent")

    async def _resume(self) -> None:
        if not self._session_id or self._seq is None:
            log.warning("Cannot RESUME — missing session_id or seq, falling back to IDENTIFY")
            await self._identify()
            return
        self._state = _State.RESUMING
        await self.send_json({
            "op": 6,
            "d": {
                "token":      self._token,
                "session_id": self._session_id,
                "seq":        self._seq,
            },
        })
        log.info("RESUME sent (session=%s, seq=%d)", self._session_id, self._seq)

                                                                          
                
                                                                          

    async def _post_ready(self, data: dict) -> None:
        await self._subscribe_guilds(data.get("guilds", []))

    async def _subscribe_guilds(self, guilds: list) -> None:
        if not guilds:
            return

                                                                                  
        ids   = [str(g["id"]) for g in guilds]
        total = len(ids)
        chunk = 50
        log.info("Subscribing to %d guilds (chunk=%d)", total, chunk)

        for i in range(0, total, chunk):
            batch = ids[i : i + chunk]
            subs  = {
                gid: {
                    "typing":     True,
                    "activities": True,
                    "threads":    True,
                }
                for gid in batch
            }
            await self.send_json({"op": 37, "d": {"subscriptions": subs}})
                                                                          
                                                             
            self._subscribed_guilds.update(int(gid) for gid in batch)
            await asyncio.sleep(0.5)

        log.info("Subscribed to %d guilds", len(self._subscribed_guilds))
