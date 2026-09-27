# Events

Gateway events are dispatched through the `EventBus`. Handlers registered
with `@bot.on_event` or `@bot.listen()` receive a parsed model object as
their first argument (or nothing if the handler takes no parameters).

---

## Registration

```python
# By function name (strip on_ prefix)
@bot.on_event
async def on_message_create(message: alterself.Message):
    ...

# Explicit name
@bot.listen("typing_start")
async def typing_handler(data):
    ...

# Manual
bot.add_listener("PRESENCE_UPDATE", my_handler)
bot.remove_listener("PRESENCE_UPDATE", my_handler)
```

---

## Event reference

### Connection

| Event | Handler arg | Description |
|---|---|---|
| `READY` | `User` — the logged-in user | Session established |
| `RESUMED` | `None` | Session resumed after reconnect |

```python
@bot.on_event
async def on_ready():
    print(f"Ready as {bot.me.username}")
```

---

### Messages

| Event | Handler arg | Description |
|---|---|---|
| `MESSAGE_CREATE` | `Message` | New message |
| `MESSAGE_UPDATE` | `Message \| None` | Message edited |
| `MESSAGE_DELETE` | `Message \| None` | Message deleted (None if not cached) |
| `MESSAGE_DELETE_BULK` | `list[Message \| None]` | Bulk delete |
| `MESSAGE_REACTION_ADD` | `dict` | Reaction added |
| `MESSAGE_REACTION_REMOVE` | `dict` | Reaction removed |

```python
@bot.on_event
async def on_message_create(message: alterself.Message):
    if message.content == "hello":
        await bot.http.send_message(
            int(message.channel_id), content="hi!"
        )
```

---

### Guilds

| Event | Handler arg | Description |
|---|---|---|
| `GUILD_CREATE` | `Guild` | Guild became available |
| `GUILD_UPDATE` | `Guild \| None` | Guild settings changed |
| `GUILD_DELETE` | `Guild \| None` | Guild became unavailable / left |
| `GUILD_MEMBER_ADD` | `Member` | New member joined |
| `GUILD_MEMBER_REMOVE` | `Member \| None` | Member left |
| `GUILD_MEMBER_UPDATE` | `Member \| None` | Member updated |

---

### Channels

| Event | Handler arg | Description |
|---|---|---|
| `CHANNEL_CREATE` | `Channel` | Channel created |
| `CHANNEL_UPDATE` | `Channel \| None` | Channel updated |
| `CHANNEL_DELETE` | `Channel \| None` | Channel deleted |
| `THREAD_CREATE` | `Channel` | Thread created |
| `THREAD_UPDATE` | `Channel \| None` | Thread updated |
| `THREAD_DELETE` | `Channel \| None` | Thread deleted |

---

### Presence / Typing

| Event | Handler arg | Description |
|---|---|---|
| `TYPING_START` | `dict` | User started typing |
| `PRESENCE_UPDATE` | `dict` | User presence changed |

---

### Relationships

| Event | Handler arg | Description |
|---|---|---|
| `RELATIONSHIP_ADD` | `dict` | Friend request / friend added |
| `RELATIONSHIP_REMOVE` | `dict` | Relationship removed |

---

### Voice

| Event | Handler arg | Description |
|---|---|---|
| `VOICE_STATE_UPDATE` | `dict` | Voice state changed |
| `VOICE_SERVER_UPDATE` | `dict` | Voice server assigned |

---

## Raw event access

If you need the raw gateway payload:

```python
@bot.listen("USER_UPDATE")
async def raw_user_update(data: dict):
    print(data)
```

The handler receives whatever the state cache parser returned — which for
most events is a model object, but falls back to the raw dict if no parser
is registered.
