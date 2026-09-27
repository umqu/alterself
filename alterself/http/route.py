
from __future__ import annotations
from typing import Any


class Endpoint:
    BASE = "https://discord.com/api/v9"

    __slots__ = ("method", "path", "bucket")

    def __init__(self, method: str, path: str, **params: Any):
        self.method = method.upper()
        self.bucket = f"{self.method}:{path}"                          
        self.path   = path.format(**{
            k: int(v) if isinstance(v, int) else v
            for k, v in params.items()
        })

    @property
    def url(self) -> str:
        return f"{self.BASE}{self.path}"

    def __repr__(self) -> str:
        return f"<Endpoint {self.method} {self.path}>"

                                                                          
           
                                                                          
    @classmethod
    def get_me(cls):
        return cls("GET", "/users/@me")

    @classmethod
    def patch_me(cls):
        return cls("PATCH", "/users/@me")

    @classmethod
    def get_me_guilds(cls, with_counts: bool = True):
        suffix = "?with_counts=true" if with_counts else ""
        return cls("GET", f"/users/@me/guilds{suffix}")

    @classmethod
    def get_user(cls, user_id: int):
        return cls("GET", "/users/{user_id}", user_id=user_id)

    @classmethod
    def get_profile(cls, user_id: int, guild_id: int | None = None):
        path = f"/users/{user_id}/profile"
        if guild_id:
            path += f"?guild_id={guild_id}"
        return cls("GET", path)

    @classmethod
    def get_settings_proto(cls):
        return cls("GET", "/users/@me/settings-proto/1")

    @classmethod
    def patch_settings_proto(cls):
        return cls("PATCH", "/users/@me/settings-proto/1")

    @classmethod
    def get_connections(cls):
        return cls("GET", "/users/@me/connections")

                                                                          
            
                                                                          
    @classmethod
    def get_guild(cls, guild_id: int):
        return cls("GET", "/guilds/{guild_id}", guild_id=guild_id)

    @classmethod
    def patch_guild(cls, guild_id: int):
        return cls("PATCH", "/guilds/{guild_id}", guild_id=guild_id)

    @classmethod
    def post_guild(cls):
        return cls("POST", "/guilds")

    @classmethod
    def delete_me_guild(cls, guild_id: int):
        return cls("DELETE", "/users/@me/guilds/{guild_id}", guild_id=guild_id)

    @classmethod
    def get_guild_channels(cls, guild_id: int):
        return cls("GET", "/guilds/{guild_id}/channels", guild_id=guild_id)

    @classmethod
    def get_guild_member(cls, guild_id: int, user_id: int):
        return cls("GET", "/guilds/{guild_id}/members/{user_id}",
                   guild_id=guild_id, user_id=user_id)

    @classmethod
    def patch_me_member(cls, guild_id: int):
        return cls("PATCH", "/guilds/{guild_id}/members/@me", guild_id=guild_id)

    @classmethod
    def get_guild_members(cls, guild_id: int):
        return cls("GET", "/guilds/{guild_id}/members", guild_id=guild_id)

    @classmethod
    def search_guild_members(cls, guild_id: int):
        return cls("GET", "/guilds/{guild_id}/members/search", guild_id=guild_id)

    @classmethod
    def delete_guild_member(cls, guild_id: int, user_id: int):
        return cls("DELETE", "/guilds/{guild_id}/members/{user_id}",
                   guild_id=guild_id, user_id=user_id)

    @classmethod
    def put_guild_ban(cls, guild_id: int, user_id: int):
        return cls("PUT", "/guilds/{guild_id}/bans/{user_id}",
                   guild_id=guild_id, user_id=user_id)

    @classmethod
    def delete_guild_ban(cls, guild_id: int, user_id: int):
        return cls("DELETE", "/guilds/{guild_id}/bans/{user_id}",
                   guild_id=guild_id, user_id=user_id)

    @classmethod
    def get_guild_bans(cls, guild_id: int):
        return cls("GET", "/guilds/{guild_id}/bans", guild_id=guild_id)

    @classmethod
    def get_guild_roles(cls, guild_id: int):
        return cls("GET", "/guilds/{guild_id}/roles", guild_id=guild_id)

    @classmethod
    def post_guild_role(cls, guild_id: int):
        return cls("POST", "/guilds/{guild_id}/roles", guild_id=guild_id)

    @classmethod
    def patch_guild_role(cls, guild_id: int, role_id: int):
        return cls("PATCH", "/guilds/{guild_id}/roles/{role_id}",
                   guild_id=guild_id, role_id=role_id)

    @classmethod
    def delete_guild_role(cls, guild_id: int, role_id: int):
        return cls("DELETE", "/guilds/{guild_id}/roles/{role_id}",
                   guild_id=guild_id, role_id=role_id)

    @classmethod
    def post_guild_invite(cls, guild_id: int):
        return cls("POST", "/guilds/{guild_id}/invites", guild_id=guild_id)

    @classmethod
    def search_guild_messages(cls, guild_id: int):
        return cls("GET", f"/guilds/{guild_id}/messages/search")

    @classmethod
    def post_join_guild(cls, invite_code: str):
        return cls("POST", f"/invites/{invite_code}")

                                                                          
              
                                                                          
    @classmethod
    def get_channel(cls, channel_id: int):
        return cls("GET", "/channels/{channel_id}", channel_id=channel_id)

    @classmethod
    def patch_channel(cls, channel_id: int):
        return cls("PATCH", "/channels/{channel_id}", channel_id=channel_id)

    @classmethod
    def delete_channel(cls, channel_id: int):
        return cls("DELETE", "/channels/{channel_id}", channel_id=channel_id)

    @classmethod
    def get_messages(cls, channel_id: int):
        return cls("GET", "/channels/{channel_id}/messages", channel_id=channel_id)

    @classmethod
    def get_message(cls, channel_id: int, message_id: int):
        return cls("GET", "/channels/{channel_id}/messages/{message_id}",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def post_message(cls, channel_id: int):
        return cls("POST", "/channels/{channel_id}/messages", channel_id=channel_id)

    @classmethod
    def patch_message(cls, channel_id: int, message_id: int):
        return cls("PATCH", "/channels/{channel_id}/messages/{message_id}",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def delete_message(cls, channel_id: int, message_id: int):
        return cls("DELETE", "/channels/{channel_id}/messages/{message_id}",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def post_bulk_delete(cls, channel_id: int):
        return cls("POST", "/channels/{channel_id}/messages/bulk-delete",
                   channel_id=channel_id)

    @classmethod
    def post_typing(cls, channel_id: int):
        return cls("POST", "/channels/{channel_id}/typing", channel_id=channel_id)

    @classmethod
    def put_pin(cls, channel_id: int, message_id: int):
        return cls("PUT", "/channels/{channel_id}/pins/{message_id}",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def delete_pin(cls, channel_id: int, message_id: int):
        return cls("DELETE", "/channels/{channel_id}/pins/{message_id}",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def get_pins(cls, channel_id: int):
        return cls("GET", "/channels/{channel_id}/pins", channel_id=channel_id)

    @classmethod
    def post_crosspost(cls, channel_id: int, message_id: int):
        return cls("POST", "/channels/{channel_id}/messages/{message_id}/crosspost",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def search_channel_messages(cls, channel_id: int):
        return cls("GET", f"/channels/{channel_id}/messages/search")

                                                                          
               
                                                                          
    @classmethod
    def put_reaction(cls, channel_id: int, message_id: int, emoji: str):
        return cls("PUT",
                   "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
                   channel_id=channel_id, message_id=message_id, emoji=emoji)

    @classmethod
    def delete_reaction(cls, channel_id: int, message_id: int, emoji: str):
        return cls("DELETE",
                   "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
                   channel_id=channel_id, message_id=message_id, emoji=emoji)

    @classmethod
    def delete_all_reactions(cls, channel_id: int, message_id: int):
        return cls("DELETE",
                   "/channels/{channel_id}/messages/{message_id}/reactions",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def get_reactions(cls, channel_id: int, message_id: int, emoji: str):
        return cls("GET",
                   "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
                   channel_id=channel_id, message_id=message_id, emoji=emoji)

                                                                          
             
                                                                          
    @classmethod
    def post_thread_from_message(cls, channel_id: int, message_id: int):
        return cls("POST",
                   "/channels/{channel_id}/messages/{message_id}/threads",
                   channel_id=channel_id, message_id=message_id)

    @classmethod
    def post_thread(cls, channel_id: int):
        return cls("POST", "/channels/{channel_id}/threads", channel_id=channel_id)

    @classmethod
    def get_active_threads(cls, channel_id: int):
        return cls("GET", "/channels/{channel_id}/threads/active",
                   channel_id=channel_id)

                                                                          
                         
                                                                          
    @classmethod
    def post_channel(cls):
        return cls("POST", "/users/@me/channels")

    @classmethod
    def get_relationships(cls):
        return cls("GET", "/users/@me/relationships")

    @classmethod
    def put_relationship(cls, user_id: int):
        return cls("PUT", "/users/@me/relationships/{user_id}", user_id=user_id)

    @classmethod
    def delete_relationship(cls, user_id: int):
        return cls("DELETE", "/users/@me/relationships/{user_id}", user_id=user_id)

                                                                          
             
                                                                          
    @classmethod
    def get_invite(cls, code: str):
        return cls("GET", f"/invites/{code}")

    @classmethod
    def delete_invite(cls, code: str):
        return cls("DELETE", f"/invites/{code}")

                                                                          
          
                                                                          
    @classmethod
    def post_login(cls):
        return cls("POST", "/auth/login")

    @classmethod
    def post_logout(cls):
        return cls("POST", "/auth/logout")

    @classmethod
    def post_register(cls):
        return cls("POST", "/auth/register")
