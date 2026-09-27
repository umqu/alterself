
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .core.enums import ActivityKind


@dataclass
class Activity:
    name:        str
    kind:        ActivityKind  = ActivityKind.PLAYING
    url:         Optional[str] = None
    details:     Optional[str] = None
    state:       Optional[str] = None
    start:       Optional[int] = None
    end:         Optional[int] = None
    large_image: Optional[str] = None
    large_text:  Optional[str] = None
    small_image: Optional[str] = None
    small_text:  Optional[str] = None
    buttons:     List[str]     = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": self.name, "type": int(self.kind)}
        if self.url:
            d["url"] = self.url
        if self.details:
            d["details"] = self.details
        if self.state:
            d["state"] = self.state
        if self.start or self.end:
            ts: Dict[str, int] = {}
            if self.start: ts["start"] = self.start
            if self.end:   ts["end"]   = self.end
            d["timestamps"] = ts
        assets: Dict[str, str] = {}
        if self.large_image: assets["large_image"] = self.large_image
        if self.large_text:  assets["large_text"]  = self.large_text
        if self.small_image: assets["small_image"] = self.small_image
        if self.small_text:  assets["small_text"]  = self.small_text
        if assets:
            d["assets"] = assets
        if self.buttons:
            d["buttons"] = self.buttons
        return d


                                                                      
                          
                                                                      

def playing(name: str, **kw) -> Activity:
    return Activity(name=name, kind=ActivityKind.PLAYING, **kw)

def streaming(name: str, url: str, **kw) -> Activity:
    return Activity(name=name, kind=ActivityKind.STREAMING, url=url, **kw)

def listening(name: str, **kw) -> Activity:
    return Activity(name=name, kind=ActivityKind.LISTENING, **kw)

def watching(name: str, **kw) -> Activity:
    return Activity(name=name, kind=ActivityKind.WATCHING, **kw)

def competing(name: str, **kw) -> Activity:
    return Activity(name=name, kind=ActivityKind.COMPETING, **kw)

def custom_status(text: str, emoji: Optional[str] = None) -> Activity:
    a = Activity(name="Custom Status", kind=ActivityKind.CUSTOM, state=text)
    if emoji:
        a.details = emoji
    return a

def spotify(
    title: str,
    artist: str,
    album: str = "",
    *,
    start: Optional[int] = None,
    end:   Optional[int] = None,
    cover_art: Optional[str] = None,
) -> Activity:
    return Activity(
        name         = "Spotify",
        kind         = ActivityKind.LISTENING,
        details      = title,
        state        = f"by {artist}",
        large_image  = cover_art or "spotify:2n7muPO0xb3RQQSPe2OJE3",
        large_text   = album,
        start        = start,
        end          = end,
    )
