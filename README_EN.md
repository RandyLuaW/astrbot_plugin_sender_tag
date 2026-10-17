<div align="center">

# Let the model know who said what

<img src="https://count.getloli.com/@astrbot_plugin_sender_tag?name=astrbot_plugin_sender_tag&theme=rule34&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto" alt="count" />

**An AstrBot plugin that prefixes every group message with `Nickname(QQ): ` before it enters the conversation history, so multi-user chats stop getting mixed up.**

![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.17-5865f2?style=flat-square)
![Version](https://img.shields.io/badge/version-1.1.0-22c55e?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square)
![Platform](https://img.shields.io/badge/platform-aiocqhttp-f97316?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-3b82f6?style=flat-square)

[简体中文](README.md) | English

<img src="logo.png" alt="Sender Tag Logo" width="180">

</div>

> 📦 **Scope**: this repository is an [AstrBot](https://github.com/AstrBotDevs/AstrBot) **plugin component**. It cannot run standalone — install it into AstrBot's `data/plugins/` and let the framework load it.

---

## Table of Contents

- [What it solves](#what-it-solves)
- [Before and after](#before-and-after)
- [Installation](#installation)
- [Configuration](#configuration)
- [How it works](#how-it-works)
- [Working with other plugins](#working-with-other-plugins)
- [Notes](#notes)
- [Version history](#version-history)

---

## What it solves

AstrBot stores conversation history **per session (per group)**: every member's message becomes a plain `user` message with **no speaker information attached**.

In a one-person group this is fine. With several people talking it breaks down:

- Alice says "I don't want to work today", Bob replies "same here" — the model cannot tell which is which, and ends up attaching the wrong mood, identity or request to the wrong person;
- Two or three topics run in parallel and answers get attributed to the wrong thread;
- After a few turns the model starts treating one member's catchphrase as another member's trait.

This plugin prefixes group messages with `Nickname(QQ): ` **before** they are sent to the LLM, and the prefix **persists with the conversation history** — so on every later turn, each historical message still carries its speaker.

---

## Before and after

Without the plugin:

```
user: I don't want to work today
user: same here, worked until 10pm yesterday
user: is your company still hiring
```

With the plugin:

```
user: Alice(123456): I don't want to work today
user: Bob(654321): same here, worked until 10pm yesterday
user: Carol(112233): is your company still hiring
```

Now the model answers Carol's hiring question instead of attaching it to Alice.

---

## Installation

### Option 1: Plugin marketplace (recommended)

AstrBot WebUI → Plugins → install from marketplace, search `astrbot_plugin_sender_tag`.

### Option 2: Releases

Download the latest `astrbot_plugin_sender_tag-vX.Y.Z.zip` from [Releases](../../releases) and upload it via "Plugins → Upload & install".

### Option 3: Clone manually

```bash
cd AstrBot/data/plugins
git clone https://github.com/RandyLuaW/astrbot_plugin_sender_tag.git
```

> [!TIP]
> No third-party dependencies. Group tagging is on by default — install and it works.

---

## Configuration

| Key | Description | Default |
|-----|-------------|---------|
| `enabled` | Master switch | `true` |
| `include_qq` | Include the QQ number in the prefix (off = nickname only, fewer tokens) | `true` |
| `tag_private_chat` | Also tag private chats | `false` |
| `max_name_len` | Truncate long nicknames, `0` = no truncation | `0` |
| `separator` | Separator between the prefix and the message body | `": "` |

---

## How it works

```
group message → AstrBot builds the LLM request (req.prompt = message text)
                      │
                      ├─ skip marker present (sender_tag_skip) ──► untouched
                      ├─ private chat with tag_private_chat off ──► untouched
                      ├─ empty prompt (image/voice only) ──► untouched
                      └─ otherwise ──► req.prompt = "Nickname(QQ): " + text
                                            │
                                            └─ persists with history, still tagged later
```

Implementation notes:

- Uses the `@filter.on_llm_request()` hook to rewrite `req.prompt` right before it reaches the model;
- **Idempotent**: if the prompt already starts with the same prefix it is left alone, so plugin reloads or stacked plugins never produce `Alice(123): Alice(123): …`;
- **Never blocks replies**: any exception is logged and the prompt stays untouched.

---

## Working with other plugins

Proactive-reply plugins (e.g. [astrbot_plugin_active_reply_ctl](https://github.com/RandyLuaW/astrbot_plugin_active_reply_ctl)) build their own template text that already says "member Alice sent a message that did not mention you". Stacking a prefix on top would give:

```
Alice(123456): member Alice sent a message that did not mention you: …
```

Such requests can set `event.set_extra("sender_tag_skip", True)` and this plugin will skip them. The plugin above already does.

---

## Notes

> [!IMPORTANT]
> This is an AstrBot plugin component and cannot run standalone.

- Tagging adds a few tokens per message; on very busy groups turn off `include_qq` or lower `max_name_len`
- Prefixes are written into persistent history; disabling the plugin later does not strip existing prefixes (usually harmless)
- Requires an adapter with a group concept (tested on `aiocqhttp`); private chats need `tag_private_chat`
- Nicknames come from the platform and may differ from group cards — keep the QQ number when unique identity matters

---

## Version history

### v1.1.0
- WebUI configuration: master switch, QQ inclusion, private-chat tagging, nickname truncation, separator
- Idempotent prefixing and load logging
- Marketplace metadata, icon and bilingual docs

### v1.0.0
- First version: prefix group messages before the LLM request, persist with history, `sender_tag_skip` support

See [CHANGELOG.md](CHANGELOG.md) for the full history.

---

## License

[MIT](LICENSE) © Randy Lua
