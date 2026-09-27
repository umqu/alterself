# Models

---

## User

| Attribute | Type | Description |
|---|---|---|
| `id` | `Flake` | Discord snowflake |
| `username` | `str` | Username |
| `discriminator` | `str` | Legacy discriminator |
| `global_name` | `str \| None` | Display name (new system) |
| `avatar` | `str \| None` | Avatar hash |
| `bot` | `bool` | Is a bot account |
| `public_flags` | `int` | Badge bitfield |
| `premium_type` | `int` | Nitro tier |

| Property | Type | Description |
|---|---|---|
| `display_name` | `str` | `global_name or username` |
| `mention` | `str` | `<@id>` |
| `avatar_url` | `str \| None` | CDN URL |
| `created_at` | `datetime` | Snowflake creation time |

---

## Guild

| Attribute | Type | Description |
|---|---|---|
| `id` | `Flake` | Guild ID |
| `name` | `str` | Guild name |
| `icon` | `str \| None` | Icon hash |
| `owner_id` | `Flake \| None` | Owner's user ID |
| `member_count` | `int` | Approximate member count |
| `premium_tier` | `int` | Boost tier (0–3) |
| `description` | `str \| None` | Guild description |

| Property | Type | Description |
|---|---|---|
| `channels` | `list[Channel]` | Cached channels |
| `members` | `list[Member]` | Cached members |
| `icon_url` | `str \| None` | CDN URL |

---

## Channel

| Attribute | Type | Description |
|---|---|---|
| `id` | `Flake` | Channel ID |
| `kind` | `ChannelKind` | Channel type |
| `name` | `str \| None` | Channel name |
| `guild_id` | `Flake \| None` | Guild this channel belongs to |
| `topic` | `str \| None` | Channel topic |
| `nsfw` | `bool` | NSFW flag |
| `parent_id` | `Flake \| None` | Category / parent thread ID |

| Property | Type | Description |
|---|---|---|
| `mention` | `str` | `<#id>` |

### DMChannel (extends Channel)

| Property | Type | Description |
|---|---|---|
| `recipient` | `User \| None` | The other user |

### GroupChannel (extends Channel)

| Property | Type | Description |
|---|---|---|
| `recipients` | `list[User]` | All recipients |
| `owner_id` | `Flake \| None` | Group owner |

---

## Message

| Attribute | Type | Description |
|---|---|---|
| `id` | `Flake` | Message ID |
| `channel_id` | `Flake` | Channel ID |
| `guild_id` | `Flake \| None` | Guild ID |
| `author` | `User \| None` | Message author |
| `content` | `str` | Text content |
| `timestamp` | `datetime \| None` | Send time |
| `edited_timestamp` | `datetime \| None` | Last edit time |
| `attachments` | `list` | File attachments |
| `embeds` | `list` | Embed objects |
| `reactions` | `list` | Reaction data |
| `pinned` | `bool` | Is pinned |
| `kind` | `MessageKind` | Message type |
| `flags` | `int` | Message flags |
| `referenced_message` | `Message \| None` | Replied-to message |

| Property | Type | Description |
|---|---|---|
| `channel` | `Channel \| None` | Cached channel |
| `guild` | `Guild \| None` | Cached guild |
| `jump_url` | `str` | Discord message link |

---

## Member

| Attribute | Type | Description |
|---|---|---|
| `id` | `Flake` | User ID |
| `guild_id` | `Flake \| None` | Guild ID |
| `nick` | `str \| None` | Nickname |
| `roles` | `list[Flake]` | Role IDs |
| `joined_at` | `str \| None` | Join timestamp |
| `deaf` | `bool` | Server deafened |
| `mute` | `bool` | Server muted |
| `pending` | `bool` | Pending membership screening |

| Property | Type | Description |
|---|---|---|
| `user` | `User \| None` | Cached User object |
| `display_name` | `str` | Nick or username |

---

## Flake (snowflake)

`Flake` is an `int` subclass with snowflake-aware properties:

```python
msg.id.created_at    # datetime UTC
msg.id.timestamp_ms  # Unix milliseconds
msg.id.worker_id
msg.id.process_id
msg.id.increment
```
