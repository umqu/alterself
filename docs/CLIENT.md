# Client

```python
alterself.Client(
    *,
    token:     str,
    prefix:    str | Callable = "!",
    owner_ids: list[int] | None = None,
    proxy:     str | None = None,
)
```

The main class. Owns the HTTP layer, the gateway connection, the state cache,
the event bus, and the command registry.

---

## Constructor parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token` | `str` | required | Discord user token |
| `prefix` | `str \| Callable` | `"!"` | Command prefix. Callable receives `(client, message)` and returns `str` |
| `owner_ids` | `list[int]` | `None` | User IDs that can use owner-only commands. Automatically includes `me.id` after READY |
| `proxy` | `str` | `None` | HTTP proxy URL e.g. `"http://user:pass@host:8080"` |

---

## Properties

| Property | Type | Description |
|---|---|---|
| `me` | `User \| None` | The logged-in user (populated after READY) |
| `guilds` | `list[Guild]` | All cached guilds |
| `latency` | `float` | Gateway heartbeat latency in seconds |
| `commands` | `list[Command]` | All registered commands |
| `cogs` | `list[Cog]` | All loaded cogs |

---

## Running

```python
# Blocking
bot.run(log_level=logging.INFO)

# Async
await bot.start()
await bot.close()

# Wait for READY before doing work
await bot.wait_until_ready(timeout=30.0)
```

---

## Event registration

### `@bot.on_event`

Maps a coroutine by name. Strip the `on_` prefix to get the event name.

```python
@bot.on_event
async def on_ready():
    ...

@bot.on_event
async def on_message_create(message):
    ...

@bot.on_event
async def on_guild_create(guild):
    ...
```

### `@bot.listen(event_name)`

Explicit event name. Case-insensitive.

```python
@bot.listen("message_create")
async def my_handler(message):
    ...
```

### `bot.add_listener(event, handler)` / `bot.remove_listener(event, handler)`

Manual registration.

---

## Commands

```python
@bot.command()
async def ping(ctx):
    await ctx.reply("pong")

@bot.command(name="hi", aliases=["hello", "hey"], brief="Say hello")
async def greet(ctx, name="world"):
    await ctx.reply(f"Hello, {name}!")
```

See [COMMANDS.md](COMMANDS.md) for the full command system.

---

## Presence

```python
import alterself

await bot.change_presence(
    status     = "online",    # "online" | "idle" | "dnd" | "invisible"
    activities = [alterself.playing("Chess")],
    afk        = False,
)
```

Status options: `online`, `idle`, `dnd`, `invisible`.

---

## Direct HTTP access

All Discord REST endpoints are available via `bot.http`:

```python
data = await bot.http.send_message(channel_id, content="hello")
await bot.http.trigger_typing(channel_id)
await bot.http.edit_me(username="newname")
guilds = await bot.http.fetch_me_guilds()
```

See [HTTP.md](HTTP.md) for the full method list.

---

## Cache access

```python
guild   = bot._cache.get_guild(guild_id)
channel = bot._cache.get_channel(channel_id)
message = bot._cache.get_message(message_id)
user    = bot._cache.get_user(user_id)
```

---

## Cogs

```python
class MyCog(alterself.Cog):
    @alterself.cmd()
    async def info(self, ctx):
        await ctx.reply(f"Running alterself v{alterself.__version__}")

bot.add_cog(MyCog())
bot.remove_cog("MyCog")
```
