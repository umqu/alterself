
from __future__ import annotations

import asyncio
import json as _json
import logging
import random
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ..spoof import SpoofEngine
from ..errors import HTTPError
from .route import Endpoint
from .ratelimit import RateLimitManager

log = logging.getLogger(__name__)

                                                                             
                       
                                                                             
                                                                          
                                                                         
                                          
                                                                             
try:
    from curl_cffi.requests import AsyncSession as _CurlSession                
    _CURL_AVAILABLE = True
    log.debug("curl_cffi available — Chrome TLS fingerprint active")
except ImportError:
    _CurlSession     = None
    _CURL_AVAILABLE  = False
    log.warning(
        "curl_cffi not installed — falling back to aiohttp (degraded TLS fingerprint). "
        "Install with: pip install curl_cffi"
    )

try:
    import aiohttp as _aiohttp                
    _AIOHTTP_AVAILABLE = True
except ImportError:
    _aiohttp           = None                 
    _AIOHTTP_AVAILABLE = False


                                                                    
                                                                        
                                                           
_DEFAULT_IMPERSONATE = "chrome136"


def _curl_impersonate_str(chrome_major: str) -> str:
    known = {
        "120": "chrome120",
        "124": "chrome124",
        "131": "chrome131",
        "133": "chrome133",
        "136": "chrome136",
    }
    return known.get(chrome_major, _DEFAULT_IMPERSONATE)


                                                                             
                        
                                                                             

class _NormalisedResponse:

    def __init__(self, status: int, headers: dict, body: bytes) -> None:
        self.status  = status
        self.headers = headers
        self._body   = body

    async def json(self, **_) -> Any:
        return _json.loads(self._body)

    async def text(self, **_) -> str:
        return self._body.decode("utf-8", errors="replace")


                                                                             
           
                                                                             

class HTTPLayer:

    API          = "https://discord.com/api/v9"
    MAX_RETRIES  = 5
    BASE_BACKOFF = 0.8             
    MAX_BACKOFF  = 60.0

    def __init__(
        self,
        token:    str,
        spoofer:  SpoofEngine,
        proxy:    Optional[str] = None,
        timeout:  int  = 30,
        pacing:   bool = True,                               
    ) -> None:
        self._token   = token
        self._spoof   = spoofer
        self._proxy   = proxy
        self._timeout = timeout
        self._rl      = RateLimitManager(pacing=pacing)
        self._session_id: Optional[str] = None
        self._closed  = False

                                       
        self._curl_session: Optional[Any]  = None
                                    
        self._aio_session:  Optional[Any]  = None

                                                              
        self._impersonate = (
            _curl_impersonate_str(spoofer.profile.chrome_major)
            if _CURL_AVAILABLE else None
        )

                                                                          
                        
                                                                          

    def _get_curl_session(self) -> Any:
        if self._curl_session is None:
            self._curl_session = _CurlSession(
                impersonate = self._impersonate or _DEFAULT_IMPERSONATE,
                timeout     = self._timeout,
            )
        return self._curl_session

    def _get_aio_session(self) -> Any:
        if self._aio_session is None or self._aio_session.closed:
            connector = _aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            self._aio_session = _aiohttp.ClientSession(
                connector = connector,
                timeout   = _aiohttp.ClientTimeout(total=self._timeout),
            )
        return self._aio_session

    async def close(self) -> None:
        self._closed = True
        if self._curl_session is not None:
            try:
                await self._curl_session.close()
            except Exception:
                pass
            self._curl_session = None
        if self._aio_session is not None and not self._aio_session.closed:
            await self._aio_session.close()
            self._aio_session = None

    def set_session_id(self, sid: str) -> None:
        self._session_id = sid

                                                                          
                     
                                                                          

    def _build_headers(
        self,
        referer: str           = "https://discord.com/channels/@me",
        ctx_key: str           = "chat",
        reason:  Optional[str] = None,
        extra:   Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        h = self._spoof.get_http_headers(referer=referer, ctx_key=ctx_key)
        if self._session_id:
            h["X-Session-Id"] = self._session_id
        if reason:
            h["X-Audit-Log-Reason"] = reason
        if extra:
            h.update(extra)
        return h

                                                                          
                                         
                                                                          

    async def _dispatch_curl(
        self,
        method:  str,
        url:     str,
        headers: Dict[str, str],
        json:    Optional[Dict[str, Any]],
    ) -> _NormalisedResponse:
        sess = self._get_curl_session()

        loop = asyncio.get_event_loop()

        def _do() -> Any:
            import json as _j
            body    = _j.dumps(json).encode() if json is not None else None
            ct_hdrs = dict(headers)
            if body is not None:
                ct_hdrs["Content-Type"] = "application/json"

            return sess.request(
                method  = method,
                url     = url,
                headers = ct_hdrs,
                content = body,
                proxy   = self._proxy,
                timeout = self._timeout,
                                                             
            )

        resp = await loop.run_in_executor(None, _do)

                                                                     
        raw_headers = dict(resp.headers)
        return _NormalisedResponse(
            status  = resp.status_code,
            headers = raw_headers,
            body    = resp.content,
        )

                                                                          
                                                
                                                                          

    async def _dispatch_aio(
        self,
        method:  str,
        url:     str,
        headers: Dict[str, str],
        json:    Optional[Dict[str, Any]],
    ) -> _NormalisedResponse:
        sess = self._get_aio_session()
        async with sess.request(
            method  = method,
            url     = url,
            headers = headers,
            json    = json,
            proxy   = self._proxy,
        ) as resp:
            body = await resp.read()
            return _NormalisedResponse(
                status  = resp.status,
                headers = dict(resp.headers),
                body    = body,
            )

                                                                          
                      
                                                                          

    async def _dispatch(
        self,
        method:  str,
        url:     str,
        headers: Dict[str, str],
        json:    Optional[Dict[str, Any]],
    ) -> _NormalisedResponse:
        if _CURL_AVAILABLE:
            return await self._dispatch_curl(method, url, headers, json)
        if _AIOHTTP_AVAILABLE:
            return await self._dispatch_aio(method, url, headers, json)
        raise RuntimeError(
            "No HTTP backend available. "
            "Install curl_cffi: pip install curl_cffi"
        )

                                                                          
                  
                                                                          

    async def request(
        self,
        ep:      Endpoint,
        *,
        json:    Optional[Dict[str, Any]] = None,
        params:  Optional[Dict[str, Any]] = None,
        reason:  Optional[str]            = None,
        referer: str = "https://discord.com/channels/@me",
        ctx_key: str = "chat",
        extra_headers: Optional[Dict[str, str]] = None,
        _attempt: int = 0,
    ) -> Any:
        if self._closed:
            raise RuntimeError("HTTPLayer is closed")

                                        
        await self._rl.pre(ep)

        url = ep.url
        if params:
            url += "?" + urlencode(params, doseq=True)

        headers = self._build_headers(
            referer=referer, ctx_key=ctx_key,
            reason=reason, extra=extra_headers,
        )

        try:
            resp = await self._dispatch(ep.method, url, headers, json)
        except HTTPError:
            raise
        except Exception as exc:
            if _attempt < self.MAX_RETRIES:
                wait = min(self.BASE_BACKOFF * 2 ** _attempt, self.MAX_BACKOFF)
                wait += random.uniform(0, wait * 0.15)
                log.warning(
                    "Network error on %s (attempt %d): %s — retry in %.2f s",
                    ep.path, _attempt + 1, exc, wait,
                )
                await asyncio.sleep(wait)
                return await self.request(
                    ep, json=json, params=params, reason=reason,
                    referer=referer, ctx_key=ctx_key,
                    extra_headers=extra_headers, _attempt=_attempt + 1,
                )
            raise HTTPError(None, str(exc))

                                             
        await self._rl.post(ep, resp)

        return await self._handle(
            resp, ep, _attempt,
            json=json, params=params, reason=reason,
            referer=referer, ctx_key=ctx_key,
            extra_headers=extra_headers,
        )

    async def _handle(self, resp: _NormalisedResponse, ep: Endpoint, attempt: int, **kwargs) -> Any:
        status = resp.status

        if status == 204:
            return None

        if status == 429:
            try:
                retry = float(resp.headers.get("Retry-After", 1.0))
            except (ValueError, TypeError):
                retry = 1.0
            log.warning("429 on %s — retry after %.2f s", ep.path, retry)
            await asyncio.sleep(retry + 0.1)
            if attempt < self.MAX_RETRIES:
                return await self.request(ep, _attempt=attempt + 1, **kwargs)
            raise HTTPError(resp, {"code": 429, "message": f"Rate limited ({retry}s)"})

        if 200 <= status < 300:
            try:
                return await resp.json()
            except Exception:
                return await resp.text()

        try:
            err = await resp.json()
        except Exception:
            err = {"message": await resp.text()}

        if 400 <= status < 500:
            raise HTTPError(resp, err)

        if 500 <= status < 600:
            if attempt < self.MAX_RETRIES:
                wait = min(self.BASE_BACKOFF * 2 ** attempt, self.MAX_BACKOFF)
                wait += random.uniform(0, wait * 0.15)
                log.warning(
                    "5xx on %s (attempt %d) — retry in %.2f s",
                    ep.path, attempt + 1, wait,
                )
                await asyncio.sleep(wait)
                return await self.request(ep, _attempt=attempt + 1, **kwargs)
            raise HTTPError(resp, err)

        raise HTTPError(resp, err)

                                                                          
                             
                                                                          

    async def send_message(
        self,
        channel_id: int,
        content: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        payload.update(kwargs)
        return await self.request(
            Endpoint.post_message(channel_id),
            json    = payload,
            referer = f"https://discord.com/channels/@me/{channel_id}",
            ctx_key = "chat",
        )

    async def edit_message(
        self,
        channel_id: int,
        message_id: int,
        content: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        payload.update(kwargs)
        return await self.request(
            Endpoint.patch_message(channel_id, message_id),
            json    = payload,
            referer = f"https://discord.com/channels/@me/{channel_id}",
        )

    async def delete_message(self, channel_id: int, message_id: int) -> None:
        await self.request(Endpoint.delete_message(channel_id, message_id))

    async def bulk_delete(self, channel_id: int, message_ids: List[int]) -> None:
        await self.request(
            Endpoint.post_bulk_delete(channel_id),
            json={"messages": [str(m) for m in message_ids]},
        )

    async def fetch_message(self, channel_id: int, message_id: int) -> Dict[str, Any]:
        return await self.request(Endpoint.get_message(channel_id, message_id))

    async def fetch_messages(
        self,
        channel_id: int,
        *,
        limit:  int = 50,
        before: Optional[int] = None,
        after:  Optional[int] = None,
        around: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        p: Dict[str, Any] = {"limit": min(limit, 100)}
        if before: p["before"] = str(before)
        if after:  p["after"]  = str(after)
        if around: p["around"] = str(around)
        return await self.request(Endpoint.get_messages(channel_id), params=p)

    async def trigger_typing(self, channel_id: int) -> None:
        await self.request(
            Endpoint.post_typing(channel_id),
            referer=f"https://discord.com/channels/@me/{channel_id}",
        )

    async def pin_message(self, channel_id: int, message_id: int) -> None:
        await self.request(Endpoint.put_pin(channel_id, message_id))

    async def unpin_message(self, channel_id: int, message_id: int) -> None:
        await self.request(Endpoint.delete_pin(channel_id, message_id))

    async def fetch_pins(self, channel_id: int) -> List[Dict[str, Any]]:
        return await self.request(Endpoint.get_pins(channel_id))

    async def crosspost_message(self, channel_id: int, message_id: int) -> Dict[str, Any]:
        return await self.request(Endpoint.post_crosspost(channel_id, message_id))

    async def add_reaction(self, channel_id: int, message_id: int, emoji: str) -> None:
        await self.request(Endpoint.put_reaction(channel_id, message_id, emoji))

    async def remove_reaction(self, channel_id: int, message_id: int, emoji: str) -> None:
        await self.request(Endpoint.delete_reaction(channel_id, message_id, emoji))

    async def clear_reactions(self, channel_id: int, message_id: int) -> None:
        await self.request(Endpoint.delete_all_reactions(channel_id, message_id))

    async def fetch_reactions(
        self, channel_id: int, message_id: int, emoji: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        return await self.request(
            Endpoint.get_reactions(channel_id, message_id, emoji),
            params={"limit": min(limit, 100)},
        )

                                                                          
                             
                                                                          

    async def fetch_channel(self, channel_id: int) -> Dict[str, Any]:
        return await self.request(Endpoint.get_channel(channel_id))

    async def edit_channel(self, channel_id: int, **kwargs) -> Dict[str, Any]:
        return await self.request(Endpoint.patch_channel(channel_id), json=kwargs)

    async def delete_channel(self, channel_id: int) -> None:
        await self.request(Endpoint.delete_channel(channel_id))

    async def search_messages(
        self,
        guild_id:   Optional[int] = None,
        channel_id: Optional[int] = None,
        **params,
    ) -> Dict[str, Any]:
        ep = (
            Endpoint.search_guild_messages(guild_id)
            if guild_id
            else Endpoint.search_channel_messages(channel_id)
        )
        return await self.request(ep, params=params)

    async def create_thread_from_message(
        self, channel_id: int, message_id: int, name: str,
        auto_archive: int = 1440, **kwargs
    ) -> Dict[str, Any]:
        payload = {"name": name, "auto_archive_duration": auto_archive}
        payload.update(kwargs)
        return await self.request(
            Endpoint.post_thread_from_message(channel_id, message_id), json=payload
        )

    async def create_thread(
        self, channel_id: int, name: str, *,
        kind: int = 11, auto_archive: int = 1440, **kwargs
    ) -> Dict[str, Any]:
        payload = {"name": name, "type": kind, "auto_archive_duration": auto_archive}
        payload.update(kwargs)
        return await self.request(Endpoint.post_thread(channel_id), json=payload)

                                                                          
                          
                                                                          

    async def fetch_me(self) -> Dict[str, Any]:
        return await self.request(Endpoint.get_me())

    async def edit_me(self, **kwargs) -> Dict[str, Any]:
        return await self.request(Endpoint.patch_me(), json=kwargs)

    async def fetch_me_guilds(self) -> List[Dict[str, Any]]:
        return await self.request(Endpoint.get_me_guilds())

    async def fetch_user(self, user_id: int) -> Dict[str, Any]:
        return await self.request(Endpoint.get_user(user_id))

    async def fetch_profile(self, user_id: int, guild_id: Optional[int] = None) -> Dict[str, Any]:
        return await self.request(Endpoint.get_profile(user_id, guild_id))

                                                                          
                           
                                                                          

    async def fetch_guild(self, guild_id: int) -> Dict[str, Any]:
        return await self.request(Endpoint.get_guild(guild_id))

    async def edit_guild(self, guild_id: int, **kwargs) -> Dict[str, Any]:
        return await self.request(Endpoint.patch_guild(guild_id), json=kwargs)

    async def create_guild(self, **kwargs) -> Dict[str, Any]:
        return await self.request(Endpoint.post_guild(), json=kwargs)

    async def leave_guild(self, guild_id: int) -> None:
        await self.request(Endpoint.delete_me_guild(guild_id))

    async def fetch_guild_channels(self, guild_id: int) -> List[Dict[str, Any]]:
        return await self.request(Endpoint.get_guild_channels(guild_id))

    async def fetch_guild_members(
        self, guild_id: int, *, limit: int = 1000, after: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        p: Dict[str, Any] = {"limit": min(limit, 1000)}
        if after:
            p["after"] = str(after)
        return await self.request(Endpoint.get_guild_members(guild_id), params=p)

    async def search_guild_members(
        self, guild_id: int, query: str, limit: int = 1
    ) -> List[Dict[str, Any]]:
        return await self.request(
            Endpoint.search_guild_members(guild_id),
            params={"query": query, "limit": min(limit, 1000)},
        )

    async def kick(self, guild_id: int, user_id: int, *, reason: Optional[str] = None) -> None:
        await self.request(Endpoint.delete_guild_member(guild_id, user_id), reason=reason)

    async def ban(
        self, guild_id: int, user_id: int, *,
        delete_message_seconds: int = 0, reason: Optional[str] = None,
    ) -> None:
        await self.request(
            Endpoint.put_guild_ban(guild_id, user_id),
            json={"delete_message_seconds": delete_message_seconds},
            reason=reason,
        )

    async def unban(self, guild_id: int, user_id: int, *, reason: Optional[str] = None) -> None:
        await self.request(Endpoint.delete_guild_ban(guild_id, user_id), reason=reason)

    async def fetch_bans(self, guild_id: int) -> List[Dict[str, Any]]:
        return await self.request(Endpoint.get_guild_bans(guild_id))

    async def fetch_roles(self, guild_id: int) -> List[Dict[str, Any]]:
        return await self.request(Endpoint.get_guild_roles(guild_id))

    async def create_role(self, guild_id: int, **kwargs) -> Dict[str, Any]:
        return await self.request(Endpoint.post_guild_role(guild_id), json=kwargs)

    async def edit_role(self, guild_id: int, role_id: int, **kwargs) -> Dict[str, Any]:
        return await self.request(Endpoint.patch_guild_role(guild_id, role_id), json=kwargs)

    async def delete_role(self, guild_id: int, role_id: int) -> None:
        await self.request(Endpoint.delete_guild_role(guild_id, role_id))

    async def join_guild(self, invite_code: str) -> Dict[str, Any]:
        return await self.request(
            Endpoint.post_join_guild(invite_code),
            referer = "https://discord.com/invite/" + invite_code,
            ctx_key = "join",
        )

                                                                          
                            
                                                                          

    async def fetch_invite(self, code: str) -> Dict[str, Any]:
        return await self.request(Endpoint.get_invite(code))

    async def delete_invite(self, code: str, *, reason: Optional[str] = None) -> None:
        await self.request(Endpoint.delete_invite(code), reason=reason)

                                                                          
                                        
                                                                          

    async def open_dm(self, recipient_id: int) -> Dict[str, Any]:
        return await self.request(
            Endpoint.post_channel(),
            json={"recipient_id": str(recipient_id)},
        )

    async def open_group_dm(
        self, access_tokens: List[str], nicks: Dict[str, str]
    ) -> Dict[str, Any]:
        return await self.request(
            Endpoint.post_channel(),
            json={"access_tokens": access_tokens, "nicks": nicks},
        )

    async def fetch_relationships(self) -> List[Dict[str, Any]]:
        return await self.request(Endpoint.get_relationships())

    async def add_friend(self, user_id: int) -> None:
        await self.request(
            Endpoint.put_relationship(user_id),
            json={"type": 1},
            ctx_key="add_friend",
        )

    async def remove_friend(self, user_id: int) -> None:
        await self.request(Endpoint.delete_relationship(user_id))

    async def block_user(self, user_id: int) -> None:
        await self.request(
            Endpoint.put_relationship(user_id),
            json={"type": 2},
        )

                                                                          
                             
                                                                          

    async def fetch_settings_proto(self) -> Dict[str, Any]:
        return await self.request(Endpoint.get_settings_proto())

    async def fetch_connections(self) -> List[Dict[str, Any]]:
        return await self.request(Endpoint.get_connections())
