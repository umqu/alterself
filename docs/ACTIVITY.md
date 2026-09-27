# Activity

Rich Presence is set via `bot.change_presence()`.

```python
import alterself

# Playing
await bot.change_presence(activities=[alterself.playing("Chess")])

# Streaming
await bot.change_presence(
    activities=[alterself.streaming("Coding", url="https://twitch.tv/me")]
)

# Listening
await bot.change_presence(activities=[alterself.listening("Lo-fi beats")])

# Watching
await bot.change_presence(activities=[alterself.watching("YouTube")])

# Competing
await bot.change_presence(activities=[alterself.competing("a Hackathon")])

# Custom status
await bot.change_presence(activities=[alterself.custom_status("Busy 🔧")])

# Fake Spotify
await bot.change_presence(
    activities=[
        alterself.spotify(
            title  = "Blinding Lights",
            artist = "The Weeknd",
            album  = "After Hours",
            start  = 1700000000000,
            end    = 1700000240000,
        )
    ]
)

# Status only (no activity)
await bot.change_presence(status="idle")
await bot.change_presence(status="dnd")
await bot.change_presence(status="invisible")
```

## Manual Activity object

```python
act = alterself.Activity(
    name        = "My Game",
    kind        = alterself.ActivityKind.PLAYING,
    details     = "In a match",
    state       = "3 kills",
    large_image = "game-logo",
    large_text  = "My Game v2.0",
    small_image = "rank-gold",
    small_text  = "Gold rank",
    start       = 1700000000000,   # Unix ms
)
await bot.change_presence(activities=[act])
```
