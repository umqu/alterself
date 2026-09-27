
from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Tuple

log = logging.getLogger(__name__)


                                                                             
                                   
                                                                             
_MEAN_DELAY       = 0.18                                                    
_STDDEV           = 0.09                                             
_MIN_DELAY        = 0.05                                             
_SAME_ROUTE_MEAN  = 0.11                                                       
_SAME_ROUTE_STD   = 0.04

_BURST_WARN       = 8                 
_BURST_WINDOW     = 3.0                                                         
_COOLDOWN_MIN     = 0.8                                              
_COOLDOWN_MAX     = 2.2


class HumanPacer:

    __slots__ = ("_history", "_last_route", "_last_ts", "_rng")

    def __init__(self) -> None:
                                                  
        self._history:    Deque[float] = deque(maxlen=_BURST_WARN + 1)
        self._last_route: Optional[str] = None
        self._last_ts:    float         = 0.0
        self._rng = random.Random()                                             

    async def pace(self, route_key: str) -> None:
        now = time.monotonic()

                                 
        if len(self._history) >= _BURST_WARN:
            oldest = self._history[0]
            if (now - oldest) < _BURST_WINDOW:
                cooldown = self._rng.uniform(_COOLDOWN_MIN, _COOLDOWN_MAX)
                log.debug(
                    "Burst detected (%d reqs in %.1f s) — cooling down %.2f s",
                    _BURST_WARN, now - oldest, cooldown,
                )
                await asyncio.sleep(cooldown)
                now = time.monotonic()

                                      
        elapsed = now - self._last_ts
        if self._last_ts > 0:
            same = (route_key == self._last_route)
            mean = _SAME_ROUTE_MEAN if same else _MEAN_DELAY
            std  = _SAME_ROUTE_STD  if same else _STDDEV
            target = max(_MIN_DELAY, self._rng.gauss(mean, std))
            gap = target - elapsed
            if gap > 0:
                await asyncio.sleep(gap)

        self._history.append(time.monotonic())
        self._last_ts    = time.monotonic()
        self._last_route = route_key


                                                                             
        
                                                                             

class _Bucket:
    __slots__ = (
        "_gate", "remaining", "reset_at", "limit",
        "hash", "_is_global", "_pending",
    )

    def __init__(self) -> None:
        self._gate      = asyncio.Lock()
        self.remaining  = 5                                
        self.reset_at   = 0.0
        self.limit      = 5
        self.hash:      Optional[str] = None
        self._is_global = False
        self._pending   = 0

    async def acquire(self) -> None:
        async with self._gate:
            self._pending += 1
            try:
                while True:
                    now = time.monotonic()

                    if self._is_global and now < self.reset_at:
                        wait = self.reset_at - now + 0.05
                        log.debug("Bucket global-limited, sleeping %.3f s", wait)
                        await asyncio.sleep(wait)
                        self._is_global = False
                        continue

                    if self.remaining <= 0 and now < self.reset_at:
                        wait = self.reset_at - now + 0.05
                        log.debug("Bucket exhausted, sleeping %.3f s", wait)
                        await asyncio.sleep(wait)
                        self.remaining = self.limit
                        continue

                    self.remaining = max(self.remaining - 1, 0)
                    break
            finally:
                self._pending -= 1

    def absorb_headers(self, headers: dict) -> None:
        try:
            if "X-RateLimit-Limit" in headers:
                self.limit = int(headers["X-RateLimit-Limit"])
            if "X-RateLimit-Remaining" in headers:
                self.remaining = max(int(headers["X-RateLimit-Remaining"]), 0)
            if "X-RateLimit-Reset-After" in headers:
                self.reset_at = time.monotonic() + float(headers["X-RateLimit-Reset-After"])
            elif "X-RateLimit-Reset" in headers:
                unix_delta    = float(headers["X-RateLimit-Reset"]) - time.time()
                self.reset_at = time.monotonic() + max(unix_delta, 0.0)
            if "X-RateLimit-Bucket" in headers:
                self.hash = headers["X-RateLimit-Bucket"]
        except (ValueError, TypeError) as exc:
            log.warning("Header parse error: %s", exc)

    def mark_global(self, retry_after: float) -> None:
        self._is_global = True
        self.reset_at   = time.monotonic() + retry_after

    @property
    def exhausted(self) -> bool:
        now = time.monotonic()
        return (self._is_global or self.remaining <= 0) and now < self.reset_at

    @property
    def resets_in(self) -> float:
        return max(self.reset_at - time.monotonic(), 0.0)


                                                                             
                  
                                                                             

class RateLimitManager:

    def __init__(self, pacing: bool = True) -> None:
        self._buckets:      Dict[str, _Bucket] = defaultdict(_Bucket)
        self._remap:        Dict[str, str]      = {}
        self._global_lock   = asyncio.Lock()
        self._global_until: float = 0.0
        self._pacer         = HumanPacer() if pacing else None

    def _bucket_for(self, endpoint) -> _Bucket:
        key        = endpoint.bucket
        mapped_key = self._remap.get(key, key)
        return self._buckets[mapped_key]

    async def pre(self, endpoint) -> None:

                                                       
        if self._pacer is not None:
            await self._pacer.pace(endpoint.bucket)

                              
        async with self._global_lock:
            now = time.monotonic()
            if now < self._global_until:
                wait = self._global_until - now + 0.05
                log.debug("Global rate limit — sleeping %.3f s", wait)
                await asyncio.sleep(wait)
                self._global_until = 0.0

                               
        await self._bucket_for(endpoint).acquire()

    async def post(self, endpoint, response) -> None:
        headers   = getattr(response, "headers", {})

        is_global = str(headers.get("X-RateLimit-Global", "")).lower() in ("true", "1", "yes")
        if is_global:
            try:
                retry = float(headers.get("Retry-After", 1.0))
            except (ValueError, TypeError):
                retry = 1.0
            async with self._global_lock:
                self._global_until = time.monotonic() + retry
            log.warning("Global rate limit — retry after %.2f s", retry)
            self._bucket_for(endpoint).mark_global(retry)
            return

        bucket = self._bucket_for(endpoint)
        bucket.absorb_headers(headers)

        new_hash = headers.get("X-RateLimit-Bucket")
        if new_hash:
            route_key = endpoint.bucket
            if self._remap.get(route_key) != new_hash:
                self._remap[route_key] = new_hash
                if new_hash not in self._buckets:
                    self._buckets[new_hash] = bucket
                log.debug("Bucket remapped %s → %s", route_key, new_hash)

    def stats(self) -> dict:
        return {
            "buckets":       len(self._buckets),
            "global_until":  self._global_until,
            "exhausted":     [k for k, b in self._buckets.items() if b.exhausted],
            "pacing":        self._pacer is not None,
        }
