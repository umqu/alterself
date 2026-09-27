# Commands

alterself parses the bot's own messages for commands. Only messages where
`author.id == me.id` are processed — it's a selfbot.

---

## Defining commands

### `@bot.command()`

```python
@bot.command(
    name    = None,         # defaults to function name
    aliases = [],           # list of alternative prefixes
    brief   = "",           # one-line description
)
async def my_command(ctx, arg1, arg2="default"):
    await ctx.reply(f"got {arg1} and {arg2}")
```

### `@alterself.cmd()` — standalone decorator for use inside Cogs

```python
class UtilCog(alterself.Cog):
    @alterself.cmd(name="serverinfo", brief="Show guild info")
    async def server_info(self, ctx):
        g = ctx.guild
        if g:
            await ctx.reply(f"**{g.name}** — {g.member_count} members")
```

---

## Arguments

Positional arguments come from splitting the message content after the prefix
and command name on spaces:

```
.echo hello world
→ ctx.args = ["hello", "world"]
→ passed to the handler as positional *args
```

If the handler signature declares named parameters, they receive the args
in order. Extra args are silently ignored; missing optional args use their
default values.

```python
@bot.command()
async def greet(ctx, name="stranger", greeting="Hello"):
    await ctx.reply(f"{greeting}, {name}!")

# .greet alice          → "Hello, alice!"
# .greet alice Goodbye  → "Goodbye, alice!"
```

---

## Context

Every command handler receives a `Context` as its first argument.

| Attribute / Method | Type | Description |
|---|---|---|
| `ctx.client` | `Client` | The bot instance |
| `ctx.message` | `Message` | The triggering message |
| `ctx.author` | `User` | Message author |
| `ctx.channel` | `Channel \| None` | Channel object |
| `ctx.guild` | `Guild \| None` | Guild object (None in DMs) |
| `ctx.channel_id` | `int` | Channel ID |
| `ctx.guild_id` | `int \| None` | Guild ID |
| `ctx.args` | `list[str]` | Parsed arguments |
| `await ctx.send(content)` | `Message` | Send a new message |
| `await ctx.reply(content)` | `Message` | Reply to the triggering message |
| `await ctx.edit(content)` | `Message` | Edit the triggering message |
| `await ctx.delete()` | `None` | Delete the triggering message |
| `await ctx.typing()` | `None` | Trigger typing indicator |

---

## Checks

Checks are predicates that gate command execution.

### Built-in checks

```python
from alterself.commands.checks import owner_only, guild_only, dm_only

@bot.command()
@alterself.check(owner_only)
async def secret(ctx):
    await ctx.reply("only the owner sees this")

@bot.command()
@alterself.check(guild_only)
async def serveronly(ctx):
    await ctx.reply("only in servers")
```

### Custom checks

```python
def no_bots(ctx):
    return ctx.author and not ctx.author.bot

@bot.command()
@alterself.check(no_bots)
async def human_only(ctx):
    await ctx.reply("you're human ✓")
```

If a check raises `CheckFailed` or returns a falsy value, the command is
silently skipped (no error message).

---

## Cogs

Cogs group related commands and listeners into a class.

```python
import alterself

class Admin(alterself.Cog):

    @alterself.cmd(brief="Purge N messages")
    async def purge(self, ctx, n="5"):
        count = int(n)
        msgs  = await ctx.client.http.fetch_messages(
            ctx.channel_id, limit=count
        )
        ids   = [int(m["id"]) for m in msgs]
        await ctx.client.http.bulk_delete(ctx.channel_id, ids)
        notice = await ctx.send(f"Deleted {len(ids)} messages.")
        await asyncio.sleep(3)
        await ctx.client.http.delete_message(ctx.channel_id, int(notice["id"]))

    def cog_load(self):
        print(f"[Admin] loaded")

    def cog_unload(self):
        print(f"[Admin] unloaded")


bot.add_cog(Admin())
```

All methods decorated with `@alterself.cmd()` are automatically registered
as commands when `add_cog()` is called.

---

## Programmatic registration

```python
# Add
bot.add_command(alterself.Command(my_func, name="test"))

# Remove
bot.remove_command("test")

# Look up
cmd = bot.get_command("test")
```
