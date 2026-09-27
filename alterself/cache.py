
from __future__ import annotations

import logging
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .core.flake import Flake
from .models.user    import User
from .models.guild   import Guild
from .models.channel import make_channel, Channel
from .models.message import Message
from .models.member  import Member

if TYPE_CHECKING:
    from .http.client import HTTPLayer

log = logging.getLogger(__name__)


class LRU(OrderedDict):

    def __init__(self, cap: int = 1000) -> None:
        super().__init__()
        self.cap = cap

    def __missing__(self, key):
        return None                                         

    def __getitem__(self, key):
        val = super().__getitem__(key)
        if val is not None:
            self.move_to_end(key)
        return val

    def __setitem__(self, key, val) -> None:
        if key in self:
                                                       
            super().__setitem__(key, val)
            self.move_to_end(key)
        else:
            super().__setitem__(key, val)
            self.move_to_end(key)
                                                                        
            if len(self) > self.cap:
                oldest = next(iter(self))
                del self[oldest]

    def get(self, key, default=None):
        try:
            val = self[key]
            return val if val is not None else default
        except KeyError:
            return default


class StateCache:

    def __init__(self, http: "HTTPLayer") -> None:
        self.http              = http
        self._users:   Dict[Flake, User]    = {}
        self._guilds:  Dict[Flake, Guild]   = {}
        self._channels:Dict[Flake, Channel] = {}
        self._messages: LRU                 = LRU(cap=5000)
        self._relationships: Dict[Flake, Any] = {}
        self.me:         Optional[User] = None
        self.session_id: Optional[str]  = None

                                                                          
               
                                                                          

    def get_guild(self, gid: int) -> Optional[Guild]:
        return self._guilds.get(Flake(gid))

    def get_channel(self, cid: int) -> Optional[Channel]:
        return self._channels.get(Flake(cid))

    def get_message(self, mid: int) -> Optional[Message]:
        return self._messages.get(Flake(mid))

    def get_user(self, uid: int) -> Optional[User]:
        return self._users.get(Flake(uid))

    @property
    def guilds(self) -> List[Guild]:
        return list(self._guilds.values())

    @property
    def channels(self) -> List[Channel]:
        return list(self._channels.values())

                                                                          
                      
                                                                          

    def _upsert_user(self, data: dict) -> User:
        fid  = Flake(data["id"])
        user = self._users.get(fid)
        if user is None:
            user = User(cache=self, data=data)
            self._users[fid] = user
        else:
            user._update(data)
        return user

    def _upsert_guild(self, data: dict) -> Guild:
        fid   = Flake(data["id"])
        guild = self._guilds.get(fid)
        if guild is None:
            guild = Guild(cache=self, data=data)
            self._guilds[fid] = guild
        else:
            guild._update(data)
        return guild

    def _upsert_channel(self, data: dict) -> Channel:
        fid = Flake(data["id"])
        ch  = self._channels.get(fid)
        if ch is None:
            ch = make_channel(self, data)
            self._channels[fid] = ch
        else:
            ch._update(data)
        return ch

    def _upsert_message(self, data: dict) -> Message:
        fid = Flake(data["id"])
        msg = self._messages.get(fid)                                       
        if msg is None:
            msg = Message(cache=self, data=data)
            self._messages[fid] = msg
        else:
            msg._update(data)
        return msg

                                                                          
                     
                                                                          

    def parse_ready(self, data: dict) -> User:
        self.session_id = data.get("session_id")
        self.me = User(cache=self, data=data["user"])
        self._users[self.me.id] = self.me

                                                                          
                                                     
        for gd in data.get("guilds", []):
            fid = Flake(gd["id"])
            if fid not in self._guilds:
                g = Guild(cache=self, data=gd)
                g._unavailable = True
                self._guilds[fid] = g

        for cd in data.get("private_channels", []):
            self._upsert_channel(cd)

        for rel in data.get("relationships", []):
            self._relationships[Flake(rel["id"])] = rel

        log.info(
            "READY — me=%s guilds=%d channels=%d",
            self.me.username, len(self._guilds), len(self._channels),
        )
        return self.me

    def parse_resumed(self, data: dict) -> None:
        log.info("RESUMED")
        return None

    def parse_user_update(self, data: dict) -> User:
        return self._upsert_user(data)

    def parse_guild_create(self, data: dict) -> Guild:
        g = self._upsert_guild(data)
        g._unavailable = False
        gid_str = str(data["id"])
        for cd in data.get("channels", []):
                                                                          
            if "guild_id" not in cd:
                cd = {**cd, "guild_id": gid_str}
            ch = self._upsert_channel(cd)
            g._channels[ch.id] = ch
        for md in data.get("members", []):
            m = Member(cache=self, data={**md, "guild_id": gid_str})
            g._members[m.id] = m
        log.debug("GUILD_CREATE %s (%s)", g.name, g.id)
        return g

    def parse_guild_update(self, data: dict) -> Optional[Guild]:
        g = self._guilds.get(Flake(data["id"]))
        if g:
            g._update(data)
        return g

    def parse_guild_delete(self, data: dict) -> Optional[Guild]:
        fid = Flake(data["id"])
        g   = self._guilds.pop(fid, None)
        if g:
            for cid in list(g._channels.keys()):
                self._channels.pop(cid, None)
        return g

    def parse_guild_member_add(self, data: dict) -> Member:
        gid   = Flake(data["guild_id"])
        guild = self._guilds.get(gid)
        m     = Member(cache=self, data=data)
        if guild:
            guild._members[m.id] = m
        return m

    def parse_guild_member_remove(self, data: dict) -> Optional[Member]:
        gid   = Flake(data["guild_id"])
        uid   = Flake(data["user"]["id"])
        guild = self._guilds.get(gid)
        if guild:
            return guild._members.pop(uid, None)
        return None

    def parse_guild_member_update(self, data: dict) -> Optional[Member]:
        gid   = Flake(data["guild_id"])
        guild = self._guilds.get(gid)
        if not guild:
            return None
        uid = Flake(data["user"]["id"])
        m   = guild._members.get(uid)
        if m:
            m._update(data)
        else:
            m = Member(cache=self, data=data)
            guild._members[m.id] = m
        return m

    def parse_guild_members_chunk(self, data: dict) -> dict:
        gid   = data.get("guild_id")
        guild = self._guilds.get(Flake(gid)) if gid else None
        if guild:
            for md in data.get("members", []):
                m = Member(cache=self, data={**md, "guild_id": gid})
                guild._members[m.id] = m
        return data

    def parse_channel_create(self, data: dict) -> Channel:
        ch = self._upsert_channel(data)
        if data.get("guild_id"):
            g = self._guilds.get(Flake(data["guild_id"]))
            if g:
                g._channels[ch.id] = ch
        return ch

    def parse_channel_update(self, data: dict) -> Optional[Channel]:
        ch = self._channels.get(Flake(data["id"]))
        if ch:
            ch._update(data)
        return ch

    def parse_channel_delete(self, data: dict) -> Optional[Channel]:
        fid = Flake(data["id"])
        ch  = self._channels.pop(fid, None)
        if ch and ch.guild_id:
            g = self._guilds.get(ch.guild_id)
            if g:
                g._channels.pop(fid, None)
        return ch

    def parse_channel_recipient_add(self, data: dict) -> None:
        ch = self._channels.get(Flake(data["channel_id"]))
        if ch and hasattr(ch, "_recipients"):
            user = self._upsert_user(data["user"])
            if user not in ch._recipients:
                ch._recipients.append(user)

    def parse_channel_recipient_remove(self, data: dict) -> None:
        ch = self._channels.get(Flake(data["channel_id"]))
        if ch and hasattr(ch, "_recipients"):
            uid = Flake(data["user"]["id"])
            ch._recipients = [r for r in ch._recipients if r.id != uid]

    def parse_thread_create(self, data: dict) -> Channel:
        return self._upsert_channel(data)

    def parse_thread_update(self, data: dict) -> Optional[Channel]:
        ch = self._channels.get(Flake(data["id"]))
        if ch:
            ch._update(data)
        return ch

    def parse_thread_delete(self, data: dict) -> Optional[Channel]:
        return self._channels.pop(Flake(data["id"]), None)

    def parse_thread_list_sync(self, data: dict) -> dict:
        for td in data.get("threads", []):
            self._upsert_channel(td)
        return data

    def parse_message_create(self, data: dict) -> Message:
        return self._upsert_message(data)

    def parse_message_update(self, data: dict) -> Optional[Message]:
        fid = Flake(data["id"])
        msg = self._messages.get(fid)
        if msg:
            msg._update(data)
            return msg
                                                                          
        if "content" in data and "author" in data:
            return self._upsert_message(data)
        return None

    def parse_message_delete(self, data: dict) -> Optional[Message]:
        return self._messages.get(Flake(data["id"]))                          
                                                                    

    def parse_message_delete_bulk(self, data: dict) -> List[Optional[Message]]:
                                                                                     
        ids = data.get("ids") or data.get("message_ids", [])
        return [self._messages.get(Flake(mid)) for mid in ids]

    def parse_reaction_add(self, data: dict) -> dict:
        return data

    def parse_reaction_remove(self, data: dict) -> dict:
        return data

    def parse_message_reaction_remove_all(self, data: dict) -> dict:
        return data

    def parse_message_reaction_remove_emoji(self, data: dict) -> dict:
        return data

    def parse_typing_start(self, data: dict) -> dict:
        return data

    def parse_presence_update(self, data: dict) -> dict:
        return data

    def parse_relationship_add(self, data: dict) -> dict:
        self._relationships[Flake(data["id"])] = data
        return data

    def parse_relationship_remove(self, data: dict) -> None:
        self._relationships.pop(Flake(data["id"]), None)
        return None

    def parse_voice_state_update(self, data: dict) -> dict:
        return data

    def parse_voice_server_update(self, data: dict) -> dict:
        return data

    def parse_call_create(self, data: dict) -> dict:
        return data

    def parse_call_update(self, data: dict) -> dict:
        return data

    def parse_call_delete(self, data: dict) -> dict:
        return data
