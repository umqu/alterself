
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import random
import re
import secrets
import time
import urllib.request as _ureq
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

                                                                             
                                                   
                                                                          
                                                                            
                        
                                                                             
_GREASE_TABLE: List[Tuple[str, str]] = [
    ('"Not A(Brand"',  "8"),
    ('"Not)A;Brand"',  "8"),
    ('"Not/A)Brand"',  "8"),
    ('"Not=A?Brand"',  "24"),
    ('"Not_A Brand"',  "24"),
    ('" Not A;Brand"', "24"),
    ('"Not A(Brand"',  "99"),                                               
    ('"Not=A?Brand"',  "99"),
    ('"Not_A Brand"',  "99"),
]

                                                           
                                                                      
_LOCALE_TZ: List[Dict[str, str]] = [
    {"locale": "en-US", "tz": "America/New_York",    "win11_prob": 0.42},
    {"locale": "en-US", "tz": "America/Chicago",     "win11_prob": 0.42},
    {"locale": "en-US", "tz": "America/Denver",      "win11_prob": 0.38},
    {"locale": "en-US", "tz": "America/Los_Angeles", "win11_prob": 0.40},
    {"locale": "en-US", "tz": "America/Phoenix",     "win11_prob": 0.35},
    {"locale": "en-GB", "tz": "Europe/London",       "win11_prob": 0.38},
    {"locale": "de",    "tz": "Europe/Berlin",       "win11_prob": 0.35},
    {"locale": "fr",    "tz": "Europe/Paris",        "win11_prob": 0.33},
    {"locale": "ja",    "tz": "Asia/Tokyo",          "win11_prob": 0.45},
    {"locale": "en-AU", "tz": "Australia/Sydney",    "win11_prob": 0.30},
    {"locale": "en-CA", "tz": "America/Toronto",     "win11_prob": 0.40},
    {"locale": "pt-BR", "tz": "America/Sao_Paulo",   "win11_prob": 0.28},
    {"locale": "nl",    "tz": "Europe/Amsterdam",    "win11_prob": 0.34},
    {"locale": "ko",    "tz": "Asia/Seoul",          "win11_prob": 0.50},
    {"locale": "pl",    "tz": "Europe/Warsaw",       "win11_prob": 0.30},
    {"locale": "es-ES", "tz": "Europe/Madrid",       "win11_prob": 0.31},
    {"locale": "ru",    "tz": "Europe/Moscow",       "win11_prob": 0.27},
    {"locale": "tr",    "tz": "Europe/Istanbul",     "win11_prob": 0.26},
    {"locale": "sv-SE", "tz": "Europe/Stockholm",    "win11_prob": 0.36},
    {"locale": "zh-TW", "tz": "Asia/Taipei",         "win11_prob": 0.44},
]

                                                                       
                                                                            
_CHROME_PATCH_POOLS: Dict[str, List[str]] = {
    "120": ["6099.109", "6099.224", "6099.234"],
    "124": ["6367.52",  "6367.60",  "6367.75"],
    "131": ["6778.62",  "6778.69",  "6778.87"],
    "133": ["6943.53",  "6943.60",  "6943.72"],
    "136": ["7103.72",  "7103.89",  "7103.114"],
}
_DEFAULT_PATCH = "0.0"                       

                                                 
                                                              
_CTX_MAP: Dict[str, str] = {
    "chat":             "chat_input_character_count",
    "guild":            "guild_channel",
    "profile":          "user_profile_modal",
    "dm":               "dm_channel_jump",
    "search":           "search_result",
    "ctx_menu":         "context_menu_jump",
    "add_friend":       "add_friend_page",
    "join":             "accept_invite_page",
    "settings":         "settings_page",
    "home":             "home",
    "notifications":    "notification_list",
    "guild_directory":  "guild_discovery",
    "thread":           "thread_channel",
    "forum":            "forum_channel",
    "activity":         "activity_shelf",
    "store":            "store_page",
    "invite":           "invite_modal",
}
_CTX_FALLBACK = "chat_input_character_count"

            
_BUILD_TTL   = 3_600         
_CHROME_TTL  = 86_400         
_CHROME_FALLBACK = "136"


@dataclass
class _Profile:
    user_agent:       str
    chrome_major:     str
    chrome_full:      str                            
    browser_version:  str                                
    locale:           str
    tz:               str
    os_version:       str                                         
    win11:            bool
    platform_version: str                                       
    webkit_version:   str                                          


                                                                             
             
                                                                             

class SpoofEngine:

                                                       
    _build_cache:     Optional[int] = None
    _build_cache_ts:  float         = 0.0
    _chrome_cache:    Optional[str] = None
    _chrome_cache_ts: float         = 0.0

    _CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

    def __init__(self, token: str) -> None:
        self._token = token

                                                                           
                                                                   
        seed_bytes = hashlib.sha256(token.encode()).digest()
        seed_int   = int.from_bytes(seed_bytes, "big")
        self._rng  = random.Random(seed_int)

                                     
        self._locale_tz: Dict[str, Any] = self._rng.choice(_LOCALE_TZ)
        self._grease:    Tuple[str, str] = self._rng.choice(_GREASE_TABLE)
        self._app_state: str = "focused"

                                                                   
        self._launch_id       = self._make_uuid()
        self._launch_sig      = self._make_uuid()
        self._hb_session_id   = self._make_uuid()
        self._installation_id = self._make_uuid()

        os.makedirs(self._CACHE_DIR, exist_ok=True)

                                     
        self.profile      = self._build_profile()
        self.build_number = self._fetch_build()

                                                                        
                  
                                                                        

    def _make_uuid(self) -> str:
        return str(uuid.UUID(int=self._rng.getrandbits(128)))

                                                                        
                    
                                                                        

    def set_state(self, focused: bool) -> None:
        self._app_state = "focused" if focused else "unfocused"

    def rotate_session(self) -> None:
        def _fresh() -> str:
            return str(uuid.UUID(bytes=secrets.token_bytes(16), version=4))

        self._launch_id     = _fresh()
        self._launch_sig    = _fresh()
        self._hb_session_id = _fresh()

    def refresh_build(self) -> int:
        SpoofEngine._build_cache_ts = 0.0
        self.build_number = self._fetch_build()
        return self.build_number

                                                                        
                      
                                                                        

    def get_http_headers(
        self,
        referer:  str = "https://discord.com/channels/@me",
        ctx_key:  str = "chat",
        extra:    Optional[Dict[str, str]] = None,
        skip_ctx: bool = False,
    ) -> Dict[str, str]:
        h: Dict[str, str] = {
            "Authorization": self._token,
            **self._common(referer),
        }
        if not skip_ctx:
            h["X-Context-Properties"] = self._ctx_props(ctx_key)
        if extra:
            h.update(extra)
        return h

    def get_multipart_headers(
        self,
        content_type: str,
        referer: str = "https://discord.com/channels/@me",
    ) -> Dict[str, str]:
        h = {
            "Authorization": self._token,
            "Content-Type":  content_type,
        }
        h.update(self._common(referer))
        return h

    def get_ws_headers(self) -> list[tuple[str, str]]:
        p = self.profile
        return [
            ("User-Agent",      p.user_agent),
            ("Accept-Language", self._accept_language()),
            ("Accept-Encoding", "gzip, deflate, br, zstd"),
            ("Origin",          "https://discord.com"),
            ("Pragma",          "no-cache"),
            ("Cache-Control",   "no-cache"),
        ]

    def get_identify_props(self) -> Dict[str, Any]:
        p = self.profile
        return {
            "os":                         "Windows",
            "browser":                    "Chrome",
            "device":                     "",
            "system_locale":              p.locale,
            "has_client_mods":            False,
            "browser_user_agent":         p.user_agent,
            "browser_version":            p.browser_version,
            "os_version":                 p.os_version,
            "referrer":                   "",
            "referring_domain":           "",
            "referrer_current":           "",
            "referring_domain_current":   "",
            "release_channel":            "stable",
            "client_build_number":        self.build_number,
            "client_event_source":        None,
            "client_launch_id":           self._launch_id,
            "launch_signature":           self._launch_sig,
            "client_app_state":           self._app_state,
            "is_fast_connect":            False,
            "gateway_connect_reasons":    "AppSkeleton",
            "installation_id":            self._installation_id,
            "native_build_number":        None,                                             
            "desktop":                    False,
        }

                                                                        
                             
                                                                        

    def _common(self, referer: str) -> Dict[str, str]:
        p = self.profile
                                                              
        try:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            ref_domain = parsed.netloc                      
        except Exception:
            ref_domain = ""

        return {
                                                                            
            "Accept":                  "*/*",
            "Accept-Language":         self._accept_language(),
            "Accept-Encoding":         "gzip, deflate, br, zstd",
            "Authorization":           self._token,
            "Content-Type":            "application/json",
            "User-Agent":              p.user_agent,
            "X-Debug-Options":         "bugReporterEnabled",
            "X-Discord-Locale":        p.locale,
            "X-Discord-Timezone":      p.tz,
            "X-Super-Properties":      self._super_props(
                                           referrer_current=referer,
                                           referring_domain_current=ref_domain,
                                       ),
            "X-Installation-Id":       self._installation_id,
            "Origin":                  "https://discord.com",
            "Referer":                 referer,
            "Sec-Ch-Ua":               self._sec_ch_ua(),
            "Sec-Ch-Ua-Mobile":        "?0",
            "Sec-Ch-Ua-Platform":      '"Windows"',
            "Sec-Ch-Ua-Platform-Version": f'"{p.platform_version}"',
            "Sec-Fetch-Dest":          "empty",
            "Sec-Fetch-Mode":          "cors",
            "Sec-Fetch-Site":          "same-origin",
            "Priority":                "u=1, i",
        }

    def _sec_ch_ua(self) -> str:
        v            = self.profile.chrome_major
        g_brand, g_v = self._grease
        grease_entry  = f'{g_brand};v="{g_v}"'
        chromium      = f'"Chromium";v="{v}"'
        chrome        = f'"Google Chrome";v="{v}"'

                                                         
        orderings = [
            [grease_entry, chromium, chrome],
            [grease_entry, chrome, chromium],
            [chromium, grease_entry, chrome],
        ]
                                                                      
        rng = random.Random()
        return ", ".join(rng.choice(orderings))

    def _super_props(
        self,
        referrer_current: str = "",
        referring_domain_current: str = "",
    ) -> str:
        p    = self.profile
        blob = {
            "os":                          "Windows",
            "browser":                     "Chrome",
            "device":                      "",
            "system_locale":               p.locale,
            "has_client_mods":             False,
            "browser_user_agent":          p.user_agent,
            "browser_version":             p.browser_version,
            "os_version":                  p.os_version,
            "referrer":                    "",
            "referring_domain":            "",
            "referrer_current":            referrer_current,
            "referring_domain_current":    referring_domain_current,
            "release_channel":             "stable",
            "client_build_number":         self.build_number,
            "client_event_source":         None,
            "client_launch_id":            self._launch_id,
            "launch_signature":            self._launch_sig,
            "client_app_state":            self._app_state,
            "client_heartbeat_session_id": self._hb_session_id,
        }
        raw = json.dumps(blob, separators=(",", ":")).encode()
        return base64.b64encode(raw).decode()

    def _ctx_props(self, key: str) -> str:
        location = _CTX_MAP.get(key, _CTX_FALLBACK)
        raw = json.dumps({"location": location}, separators=(",", ":")).encode()
        return base64.b64encode(raw).decode()

    def _accept_language(self) -> str:
        loc  = self.profile.locale
        lang = loc.split("-")[0]

        if loc == "en-US":
            return "en-US,en;q=0.9"
        if loc.startswith("en-"):
            return f"{loc},en;q=0.9,en-US;q=0.8"
                                                          
        return f"{loc},{lang};q=0.9,en;q=0.8,en-US;q=0.7"

                                                                        
                          
                                                                        

    def _build_profile(self) -> _Profile:
        major = self._fetch_chrome_major()
        lt    = self._locale_tz

                                                           
        patch_pool = _CHROME_PATCH_POOLS.get(major, [_DEFAULT_PATCH])
        patch      = self._rng.choice(patch_pool)
        full_ver   = f"{major}.0.{patch}"

                                                        
        win11 = self._rng.random() < lt.get("win11_prob", 0.35)
        os_version = "10.0.22631" if win11 else "10"
        platform_version = "15.0.0" if win11 else "10.0.0"

                                                                              
        webkit_version = "537.36"

        ua = (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/{webkit_version} (KHTML, like Gecko) "
            f"Chrome/{full_ver} Safari/{webkit_version}"
        )

        return _Profile(
            user_agent       = ua,
            chrome_major     = major,
            chrome_full      = full_ver,
            browser_version  = full_ver,
            locale           = lt["locale"],
            tz               = lt["tz"],
            os_version       = os_version,
            win11            = win11,
            platform_version = platform_version,
            webkit_version   = webkit_version,
        )

                                                                        
                        
                                                                        

    def _fetch_chrome_major(self) -> str:
        now = time.time()
        if SpoofEngine._chrome_cache and now - SpoofEngine._chrome_cache_ts < _CHROME_TTL:
            return SpoofEngine._chrome_cache

        disk = os.path.join(self._CACHE_DIR, "chrome_ver.json")
        try:
            req = _ureq.Request(
                "https://versionhistory.googleapis.com/v1/chrome/platforms/win"
                "/channels/stable/versions/all/releases?filter=endtime=none",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with _ureq.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
            releases = data.get("releases", [])
            if not releases:
                raise ValueError("empty releases list")
            latest = max(
                releases,
                key=lambda r: [int(p) for p in r["version"].split(".")],
            )
            major = latest["version"].split(".")[0]
            SpoofEngine._chrome_cache    = major
            SpoofEngine._chrome_cache_ts = now
            try:
                with open(disk, "w") as f:
                    json.dump({"major": major, "ts": now}, f)
            except OSError:
                pass
            log.debug("Chrome major resolved: %s", major)
            return major
        except Exception as exc:
            log.warning("Chrome version fetch failed (%s), checking disk cache", exc)

        try:
            if os.path.exists(disk):
                with open(disk) as f:
                    cached = json.load(f)
                major = str(cached["major"])
                SpoofEngine._chrome_cache    = major
                SpoofEngine._chrome_cache_ts = now
                return major
        except Exception:
            pass

        log.warning("Using Chrome fallback: %s", _CHROME_FALLBACK)
        return _CHROME_FALLBACK

    def _fetch_build(self) -> int:
        now = time.time()
        if SpoofEngine._build_cache and now - SpoofEngine._build_cache_ts < _BUILD_TTL:
            return SpoofEngine._build_cache

        disk = os.path.join(self._CACHE_DIR, "build_num.json")

        try:
            req1 = _ureq.Request(
                "https://discord.com/login",
                headers={"User-Agent": self.profile.user_agent},
            )
            with _ureq.urlopen(req1, timeout=30) as r1:
                html = r1.read().decode("utf-8", errors="replace")

            scripts = re.findall(r'<script[^>]+src="(/assets/[^"]+\.js)"', html)

                                                                      
            if not scripts:
                raise ValueError("No script tags found in Discord login page")

            patterns = [
                r'buildNumber\s*[=:]\s*"?(\d{5,7})"?',
                r'"buildNumber","(\d{5,7})"',
                r'CLIENT_BUILD_NUMBER\s*[=:]\s*(\d{5,7})',
                r'build_number[":\s=]+(\d{5,7})',
                r'"(\d{6,7})"\s*,\s*"stable"',
                r'build[_-]?num(?:ber)?\s*[=:]\s*(\d{5,7})',
                r',(\d{6}),',                                                   
            ]
            for path in reversed(scripts):
                try:
                    req2 = _ureq.Request(
                        f"https://discord.com{path}",
                        headers={"User-Agent": self.profile.user_agent},
                    )
                    with _ureq.urlopen(req2, timeout=30) as r2:
                        js = r2.read().decode("utf-8", errors="replace")
                except Exception:
                    continue
                for pat in patterns:
                    m = re.search(pat, js)
                    if m:
                        build = int(m.group(1))
                                                                      
                        if not (10_000 <= build <= 9_999_999):
                            continue
                        SpoofEngine._build_cache    = build
                        SpoofEngine._build_cache_ts = now
                        try:
                            with open(disk, "w") as f:
                                json.dump({"build": build, "ts": now}, f)
                        except OSError:
                            pass
                        log.info("Build number resolved: %d", build)
                        return build
        except Exception as exc:
            log.warning("Build number scrape failed: %s", exc)

                             
        try:
            if os.path.exists(disk):
                with open(disk) as f:
                    cached = json.load(f)
                build = int(cached["build"])
                SpoofEngine._build_cache    = build
                SpoofEngine._build_cache_ts = now
                log.info("Build number from disk cache: %d", build)
                return build
        except Exception:
            pass

        fallback = 612808
        log.warning("Using build number fallback: %d", fallback)
        SpoofEngine._build_cache    = fallback
        SpoofEngine._build_cache_ts = now
        return fallback
