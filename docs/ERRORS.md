# Errors

All alterself exceptions inherit from `AlterselfError`.

```
AlterselfError
├── HTTPError              — HTTP request failed (4xx, 5xx)
├── GatewayError           — WebSocket-level failure
│   └── SessionClosed      — Gateway connection closed
├── CommandError           — Command pipeline failure
│   ├── CheckFailed        — A check decorator returned falsy
│   ├── ConversionFailed   — Type converter raised an exception
│   ├── CommandNotFound    — No command matched the invocation
│   └── MissingArgument    — Required argument absent
└── CaptchaChallenge       — Discord requires a captcha
```

---

## HTTPError

Raised when a Discord API request returns 4xx or 5xx.

```python
from alterself import HTTPError

try:
    await bot.http.send_message(channel_id, content="hello")
except HTTPError as e:
    print(e.status)    # HTTP status code
    print(e.code)      # Discord error code
    print(e.text)      # Discord error message
```

Common Discord error codes:
- `10003` — Unknown channel
- `10004` — Unknown guild
- `10008` — Unknown message
- `50001` — Missing access
- `50013` — Missing permissions
- `50035` — Invalid form body

---

## SessionClosed

```python
from alterself import SessionClosed

try:
    await bot.start()
except SessionClosed as e:
    print(e.code)   # WebSocket close code
```

Fatal codes (will not reconnect):
- `4004` — Token invalid
- `4010` — Invalid shard
- `4011` — Sharding required
- `4012` — Invalid API version
- `4013` — Invalid intents
- `4014` — Disallowed intents

---

## CheckFailed

Raised when a command check returns `False`. alterself catches this
internally and silently skips the command; you only need to handle it
if you add a custom error handler.

---

## CaptchaChallenge

```python
from alterself import CaptchaChallenge

try:
    await bot.http.join_guild("invite")
except CaptchaChallenge as e:
    print(e.sitekey)   # hCaptcha site key
    print(e.rqdata)    # Additional challenge data
```
