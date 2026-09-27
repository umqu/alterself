
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Callable, Optional

log = logging.getLogger(__name__)


class HeartbeatManager:
    __slots__ = (
        "_ws", "_interval_ms", "_seq_getter",
        "_task", "_stop", "_ack_event",
        "_sent_at", "latency", "_pending",
    )

    def __init__(
        self,
        ws,
        interval_ms: float,
        seq_getter: Callable[[], Optional[int]],
    ) -> None:
        self._ws          = ws
        self._interval_ms = interval_ms
        self._seq_getter  = seq_getter
        self._task:  Optional[asyncio.Task] = None
        self._stop        = asyncio.Event()
        self._ack_event   = asyncio.Event()
        self._sent_at:    float = 0.0
        self.latency:     float = 0.0
        self._pending:    bool  = False

                                                                          

    def start(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._stop.clear()
        self._ack_event.clear()
        self._pending = False
        self._task = asyncio.create_task(
            self._loop(), name="alterself:heartbeat"
        )
        log.debug("Heartbeat started — interval %.0f ms", self._interval_ms)

    def stop(self) -> None:
        self._stop.set()
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def ack(self) -> None:
        if self._pending:
            self.latency = time.monotonic() - self._sent_at
        self._pending = False
        self._ack_event.set()
        log.debug("HB ACK — latency %.1f ms", self.latency * 1000)

                                                                          

    async def _send_one(self) -> None:
        seq = self._seq_getter()
                                                                         
                                                             
        self._ack_event.clear()
        await self._ws.send_json({"op": 1, "d": seq})
        self._sent_at = time.monotonic()
        self._pending = True
        log.debug("HB sent (seq=%s)", seq)

    async def _loop(self) -> None:
        interval_s = self._interval_ms / 1000.0

                                                                               
        jitter = random.random() * interval_s
        log.debug("First HB in %.3f s", jitter)
        try:
            await asyncio.wait_for(asyncio.shield(self._stop.wait()), timeout=jitter)
            return                            
        except asyncio.TimeoutError:
            pass

        while not self._stop.is_set():
            await self._send_one()

                                                                               
                                                                              
                                                                   
            ack_task   = asyncio.ensure_future(self._ack_event.wait())
            sleep_task = asyncio.ensure_future(asyncio.sleep(interval_s))
            stop_task  = asyncio.ensure_future(self._stop.wait())

            try:
                done, pending = await asyncio.wait(
                    {ack_task, sleep_task, stop_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except asyncio.CancelledError:
                for t in (ack_task, sleep_task, stop_task):
                    t.cancel()
                return

                                                               
            for t in (ack_task, sleep_task, stop_task):
                if not t.done():
                    t.cancel()

            if self._stop.is_set():
                return

                                                                        
                                                                         
                                                                          
            if sleep_task in done and not self._ack_event.is_set():
                log.error(
                    "Heartbeat ACK not received within %.0f ms — "
                    "session zombied, forcing reconnect",
                    self._interval_ms,
                )
                raise ConnectionResetError("Gateway heartbeat ACK timed out")

                                                                             
                                                                                
            elapsed   = time.monotonic() - self._sent_at
            remaining = max(0.0, interval_s - elapsed - 0.01)
            if remaining > 0 and not self._stop.is_set():
                try:
                    await asyncio.wait_for(
                        asyncio.shield(self._stop.wait()),
                        timeout=remaining,
                    )
                    return              
                except asyncio.TimeoutError:
                    pass

    @property
    def alive(self) -> bool:
        return not self._pending
