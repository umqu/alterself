# HTTP

`bot.http` exposes every Discord REST endpoint as a typed async method.
All requests go through the rate limit manager and header spoofer automatically.

---

## Messages

```python
# Send
data = await bot.http.send_message(channel_id, content="hello")
data = await bot.http.send_message(
    channel_id,
    content    = "with embed",
    embeds     = [{"title": "hi", "description": "world", "color": 0xFF6B6B}],
    components = [],
)

# Edit
data = await bot.http.edit_message(channel_id, message_id, content="edited")

# Delete
await bot.http.delete_message(channel_id, message_id)

# Bulk delete (bot must have Manage Messages — selfbot: only your own messages)
await bot.http.bulk_delete(channel_id, [msg_id_1, msg_id_2])

# Fetch
msg  = await bot.http.fetch_message(channel_id, message_id)
msgs = await bot.http.fetch_messages(
    channel_id,
    limit  = 50,      # max 100
    before = msg_id,  # optional
    after  = msg_id,  # optional
    around = msg_id,  # optional
)

# Pins
await bot.http.pin_message(channel_id, message_id)
await bot.http.unpin_message(channel_id, message_id)
pins = await bot.http.fetch_pins(channel_id)

# Crosspost (announcement channels)
await bot.http.crosspost_message(channel_id, message_id)

# Typing
await bot.http.trigger_typing(channel_id)

# Search
results = await bot.http.search_messages(
    guild_id   = guild_id,
    content    = "hello",
    author_id  = user_id,
    channel_id = channel_id,
)
```

---

## Reactions

```python
await bot.http.add_reaction(channel_id, message_id, "👍")
await bot.http.add_reaction(channel_id, message_id, "custom_emoji:123456789")
await bot.http.remove_reaction(channel_id, message_id, "👍")
await bot.http.clear_reactions(channel_id, message_id)
users = await bot.http.fetch_reactions(channel_id, message_id, "👍")
```

---

## Channels

```python
ch   = await bot.http.fetch_channel(channel_id)
ch   = await bot.http.edit_channel(channel_id, name="new-name", topic="new topic")
await bot.http.delete_channel(channel_id)

# Threads
thread = await bot.http.create_thread_from_message(
    channel_id, message_id, "Thread name", auto_archive=1440
)
thread = await bot.http.create_thread(
    channel_id, "New thread",
    kind=11,             # PUBLIC_THREAD
    auto_archive=10080,  # 7 days
)
```

---

## Users

```python
me      = await bot.http.fetch_me()
user    = await bot.http.fetch_user(user_id)
profile = await bot.http.fetch_profile(user_id)
profile = await bot.http.fetch_profile(user_id, guild_id=guild_id)

# Edit own profile
me = await bot.http.edit_me(
    username   = "newname",
    global_name= "Display Name",
    # avatar: pass base64-encoded "data:image/png;base64,..." string
)

guilds  = await bot.http.fetch_me_guilds()
conns   = await bot.http.fetch_connections()
```

---

## Guilds

```python
g    = await bot.http.fetch_guild(guild_id)
g    = await bot.http.edit_guild(guild_id, name="New Name")
await bot.http.leave_guild(guild_id)

chs  = await bot.http.fetch_guild_channels(guild_id)
mems = await bot.http.fetch_guild_members(guild_id, limit=1000)
mems = await bot.http.search_guild_members(guild_id, query="alice")

# Moderation
await bot.http.kick(guild_id, user_id, reason="spam")
await bot.http.ban(guild_id, user_id, delete_message_seconds=86400, reason="spam")
await bot.http.unban(guild_id, user_id)
bans = await bot.http.fetch_bans(guild_id)

# Roles
roles  = await bot.http.fetch_roles(guild_id)
role   = await bot.http.create_role(guild_id, name="VIP", color=0xFFD700)
role   = await bot.http.edit_role(guild_id, role_id, name="Elite")
await bot.http.delete_role(guild_id, role_id)

# Join via invite
await bot.http.join_guild("abc123")
```

---

## Invites

```python
inv  = await bot.http.fetch_invite("abc123")
await bot.http.delete_invite("abc123")
```

---

## DMs and Relationships

```python
dm   = await bot.http.open_dm(user_id)
rels = await bot.http.fetch_relationships()
await bot.http.add_friend(user_id)
await bot.http.remove_friend(user_id)
await bot.http.block_user(user_id)
```

---

## Raw request

For endpoints not covered by a typed method:

```python
from alterself.http.route import Endpoint

ep   = Endpoint("GET", "/users/@me/affinities/guilds")
data = await bot.http.request(ep)
```

---

## Rate limits

Handled automatically. The `RateLimitManager` tracks per-bucket and global
rate limits and waits before firing the next request. You never need to
sleep manually.

Stats:
```python
print(bot.http._rl.stats())
# {'buckets': 12, 'global_until': 0.0, 'exhausted': []}
```
