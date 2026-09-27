# alterself v1.0

A clean, Pythonic Discord selfbot library built from scratch.  
Full browser fingerprint spoofing — headers, gateway identify, super-properties, sec-ch-ua, locale/timezone — all coherent, session-stable, and indistinguishable from a real Chrome client.

```
pip install git+https://github.com/umqu/alterself.git
```

---

## Quick start

```python
import alterself

bot = alterself.Client(token="YOUR_TOKEN", prefix="!")

@bot.on_event
async def on_ready():
    print(f"Logged in as {bot.me.username}")

@bot.command()
async def ping(ctx):
    await ctx.reply("pong 🏓")

@bot.command(name="echo", aliases=["say"])
async def echo_cmd(ctx, *args):
    await ctx.reply(" ".join(args))

bot.run()
```

---

## Docs

| Document | Coverage |
|---|---|
| [GETTING_STARTED.md](docs/GETTING_STARTED.md) | Installation, first bot, running |
| [SPOOFING.md](docs/SPOOFING.md) | How the fingerprint engine works |
| [CLIENT.md](docs/CLIENT.md) | `Client` API reference |
| [COMMANDS.md](docs/COMMANDS.md) | Commands, Cogs, Context |
| [EVENTS.md](docs/EVENTS.md) | All gateway events |
| [MODELS.md](docs/MODELS.md) | User, Guild, Channel, Message, Member |
| [ACTIVITY.md](docs/ACTIVITY.md) | Rich Presence builders |
| [HTTP.md](docs/HTTP.md) | Direct HTTP layer access |
| [ERRORS.md](docs/ERRORS.md) | Exception hierarchy |
| [EXAMPLES.md](docs/EXAMPLES.md) | Full working examples |

---

## Spoofing at a glance

alterself generates a **coherent, seeded browser identity** per token:

- **User-Agent** — real Chrome version pulled live from the Chromium Releases API, cached 24 h  
- **X-Super-Properties** — base64 JSON blob matching Discord's `getSuperProperties()` exactly, including `client_launch_id`, `launch_signature`, `client_heartbeat_session_id`  
- **sec-ch-ua** — GREASE brand rotated per session from the authentic set, ordering shuffled across three valid variants  
- **X-Context-Properties** — per-action location token injected on every HTTP request  
- **Build number** — scraped live from Discord's login page JS assets, disk-cached 1 h  
- **Gateway IDENTIFY** — `properties` block mirrors super-props byte for byte  
- **Locale / timezone** — paired consistently (e.g. `en-US` + `America/Chicago`)  
- **Session UUIDs** — seeded from `MD5(token)` for session stability; rotated on each new READY

---

## Requirements

- Python ≥ 3.11  
- aiohttp ≥ 3.9  
- websockets ≥ 12
