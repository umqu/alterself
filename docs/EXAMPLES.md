# Examples

---

## Basic ping/pong

```python
import alterself

bot = alterself.Client(token="TOKEN", prefix=".")

@bot.on_event
async def on_ready():
    print(f"Ready — {bot.me.username}")

@bot.command()
async def ping(ctx):
    await ctx.reply(f"pong | {bot.latency * 1000:.1f} ms")

bot.run()
```

---

## Echo + delete original

```python
@bot.command(aliases=["say"])
async def echo(ctx, *args):
    await ctx.delete()                      # delete own message
    await bot.http.send_message(
        ctx.channel_id,
        content=" ".join(args)
    )
```

---

## Presence cycling

```python
import asyncio, alterself

bot = alterself.Client(token="TOKEN", prefix="!")

ACTIVITIES = [
    alterself.playing("Chess"),
    alterself.listening("Spotify"),
    alterself.watching("YouTube"),
    alterself.custom_status("Coding something cool 👨‍💻"),
]

@bot.on_event
async def on_ready():
    asyncio.create_task(cycle_presence())

async def cycle_presence():
    i = 0
    while True:
        await bot.change_presence(activities=[ACTIVITIES[i % len(ACTIVITIES)]])
        i += 1
        await asyncio.sleep(60)

bot.run()
```

---

## Cog with admin commands

```python
import asyncio
import alterself
from alterself.commands.checks import owner_only

class AdminCog(alterself.Cog):

    @alterself.cmd(brief="Purge N of your messages")
    @alterself.check(owner_only)
    async def purge(self, ctx, n="10"):
        count  = min(int(n), 100)
        msgs   = await ctx.client.http.fetch_messages(
            ctx.channel_id, limit=count
        )
        my_ids = [
            int(m["id"]) for m in msgs
            if m.get("author", {}).get("id") == str(ctx.client.me.id)
        ]
        for mid in my_ids:
            await ctx.client.http.delete_message(ctx.channel_id, mid)
            await asyncio.sleep(0.4)   # avoid rate limits
        notice = await ctx.send(f"Deleted {len(my_ids)} messages.")
        await asyncio.sleep(3)
        await ctx.client.http.delete_message(
            ctx.channel_id, int(notice["id"])
        )

    @alterself.cmd(brief="Show server info")
    async def sinfo(self, ctx):
        g = ctx.guild
        if not g:
            await ctx.reply("Not in a server.")
            return
        await ctx.reply(
            f"**{g.name}**\n"
            f"ID: `{g.id}`\n"
            f"Members: {g.member_count}\n"
            f"Boost tier: {g.premium_tier}"
        )


bot = alterself.Client(token="TOKEN", prefix=".")
bot.add_cog(AdminCog())
bot.run()
```

---

## Message logger

```python
import alterself, datetime

bot = alterself.Client(token="TOKEN", prefix=";")

@bot.on_event
async def on_message_create(message: alterself.Message):
    if message.guild_id:
        return   # only log DMs
    ts   = datetime.datetime.now().strftime("%H:%M:%S")
    who  = message.author.username if message.author else "?"
    print(f"[{ts}] DM from {who}: {message.content}")

bot.run()
```

---

## Spoof info command

```python
@bot.command(aliases=["whoami"])
async def spoof(ctx):
    s = ctx.client._spoof
    await ctx.reply(
        f"**Fingerprint**\n"
        f"UA: `{s.profile.user_agent}`\n"
        f"Locale: `{s.profile.locale}` / TZ: `{s.profile.tz}`\n"
        f"Build: `{s.build_number}`\n"
        f"Installation ID: `{s._installation_id}`"
    )
```

---

## Auto-react to specific user

```python
TARGET_USER = 123456789012345678
EMOJI       = "❤️"

@bot.on_event
async def on_message_create(message: alterself.Message):
    if message.author and int(message.author.id) == TARGET_USER:
        await bot.http.add_reaction(
            int(message.channel_id),
            int(message.id),
            EMOJI,
        )
```

---

## Guild joiner

```python
import alterself

async def join_many(token, codes):
    bot  = alterself.Client(token=token, prefix="!")
    # Don't need the event loop — just use HTTP directly
    import asyncio

    spoof = bot._spoof
    http  = bot.http

    for code in codes:
        try:
            data = await http.join_guild(code)
            print(f"[+] Joined {data.get('guild', {}).get('name', code)}")
        except alterself.HTTPError as e:
            print(f"[-] Failed {code}: {e}")
        await asyncio.sleep(1.5)

    await http.close()

import asyncio
asyncio.run(join_many("TOKEN", ["invite1", "invite2"]))
```

---

## Refresh build number manually

```python
@bot.command()
async def refresh(ctx):
    old   = ctx.client._spoof.build_number
    new   = ctx.client._spoof.refresh_build()
    await ctx.reply(f"Build: `{old}` → `{new}`")
```
