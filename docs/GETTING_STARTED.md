# Getting Started

## Install

```bash
pip install alterself
# or from source
git clone https://github.com/you/alterself
cd alterself
pip install -e .
```

## Your first bot

```python
import alterself

bot = alterself.Client(
    token  = "YOUR_USER_TOKEN",
    prefix = ".",
)

@bot.on_event
async def on_ready():
    print(f"[+] Ready — logged in as {bot.me.username}#{bot.me.discriminator}")
    print(f"[+] Build number: {bot._spoof.build_number}")
    print(f"[+] Spoofed UA: {bot._spoof.profile.user_agent}")

@bot.command()
async def ping(ctx):
    await ctx.reply(f"pong | latency {bot.latency * 1000:.1f} ms")

bot.run()
```

## Token

Get your user token from the Discord web client:
1. Open DevTools (F12) → Application → Storage → Local Storage → `https://discord.com`  
2. Find `token` key  
3. Copy the value (no quotes)

**Never share your token.**

## Prefix

The prefix can be a string or an async function:

```python
# Static
bot = alterself.Client(token="...", prefix="!")

# Dynamic — different prefix per guild
async def get_prefix(client, message):
    if message.guild_id == 123456789:
        return "?"
    return "!"

bot = alterself.Client(token="...", prefix=get_prefix)
```

## Logging

`bot.run()` sets up basic logging to stdout. Pass `log_level`:

```python
import logging
bot.run(log_level=logging.DEBUG)   # very verbose
bot.run(log_level=logging.WARNING) # quiet
```

## Async entry point

If you're already inside an async context:

```python
async def main():
    bot = alterself.Client(token="...", prefix="!")

    @bot.on_event
    async def on_ready():
        print("ready")

    await bot.start()   # blocks until close
```

## Environment variable pattern

```python
import os, alterself

bot = alterself.Client(
    token  = os.environ["DISCORD_TOKEN"],
    prefix = os.environ.get("PREFIX", "!"),
)
```
