# CMDOP Bots

**Multi-channel bot integrations for remote machine access.**

Control your servers via Telegram, Discord, or Slack. Simple, reliable, open-source.

> 📖 **Read the article**: [PicoClaw and OpenClaw Are Not Infrastructure: The $10 AI Agent Myth](https://medium.com/@reformsai/picoclaw-and-openclaw-are-not-infrastructure-the-10-ai-agent-myth-43d43e0726e3)

## Install

```bash
pip install cmdop-bot

# With Telegram support
pip install cmdop-bot[telegram]

# With Discord support
pip install cmdop-bot[discord]

# With Slack support
pip install cmdop-bot[slack]

# With all channels
pip install cmdop-bot[all]
```

## Quick Start

### Telegram Bot

```python
from cmdop_bots.channels.telegram import TelegramBot

bot = TelegramBot(
    token="YOUR_TELEGRAM_BOT_TOKEN",
    cmdop_api_key="YOUR_CMDOP_API_KEY",
    allowed_users=[123456789],  # Your Telegram user ID
    machine="my-server",  # Optional: target machine
)

bot.run()
```

### Discord Bot

```python
from cmdop_bots.channels.discord import DiscordBot

bot = DiscordBot(
    token="YOUR_DISCORD_BOT_TOKEN",
    cmdop_api_key="YOUR_CMDOP_API_KEY",
    guild_ids=[123456789],  # Optional: for faster command sync
)

bot.run()
```

### Slack App

```python
from cmdop_bots.channels.slack import SlackApp

app = SlackApp(
    bot_token="xoxb-YOUR-BOT-TOKEN",
    app_token="xapp-YOUR-APP-TOKEN",
    cmdop_api_key="YOUR_CMDOP_API_KEY",
)

app.run()
```

## Commands

| Channel | Command | Description |
|---------|---------|-------------|
| Telegram | `/shell <cmd>` | Execute shell command |
| Telegram | `/exec <cmd>` | Alias for /shell |
| Telegram | `/agent <task>` | Run AI agent task |
| Telegram | `/ls [path]` | List directory |
| Telegram | `/cat <path>` | Read file |
| Telegram | `/machine <host>` | Set target machine |
| Discord | `/shell <cmd>` | Execute shell command |
| Discord | `/agent <task>` | Run AI agent task |
| Discord | `/ls [path]` | List directory |
| Discord | `/cat <path>` | Read file |
| Discord | `/machine <host>` | Set target machine |
| Discord | `/status` | Show connection status |
| Slack | `/cmdop shell <cmd>` | Execute shell command |
| Slack | `/cmdop agent <task>` | Run AI agent task |
| Slack | `/cmdop ls [path]` | List directory |
| Slack | `/cmdop cat <path>` | Read file |
| Slack | `/cmdop machine <host>` | Set target machine |
| Slack | `/cmdop status` | Show connection status |

## Features

### Telegram
- MarkdownV2 formatting
- Code block syntax highlighting
- Typing indicators
- User allowlist

### Discord
- Slash commands
- Rich embeds
- Ephemeral messages for sensitive data
- Deferred responses for slow operations
- Guild-specific command sync

### Slack
- Socket Mode (no public webhooks needed)
- Block Kit messages
- Interactive buttons
- Slash command handling

## Handlers

Use handlers directly in your own bot:

```python
from cmdop_bots.handlers import ShellHandler, AgentHandler, FilesHandler

# Create handlers
shell = ShellHandler(cmdop_api_key="cmd_xxx", machine="my-server")
agent = AgentHandler(cmdop_api_key="cmd_xxx")
files = FilesHandler(cmdop_api_key="cmd_xxx")

# Use in your handler
async def handle_command(command, send):
    await shell.handle(command, send)

# Clean up
await shell.close()
await agent.close()
await files.close()
```

## Permissions

Control who can use your bot:

```python
from cmdop_bots import PermissionManager, PermissionLevel

pm = PermissionManager()

# Add admin (full access)
pm.add_admin("telegram:123456789")

# Grant execute permission
pm.grant("discord:987654321", machine="prod-server", level=PermissionLevel.EXECUTE)

# Use with bot
bot = TelegramBot(
    token="...",
    cmdop_api_key="...",
    permissions=pm,
)
```

## Architecture

```
+--------------+
|  Telegram    |
|  Discord     |------> CMDOP SDK ------> Your Servers
|  Slack       |
+--------------+
```

- **Simple**: Each bot is < 200 lines of code
- **Reliable**: Proper error handling, reconnection
- **Secure**: Permission system, user allowlists

## Development

```bash
# Clone repository
git clone https://github.com/commandoperator/cmdop-bot
cd cmdop-bot

# Install dev dependencies
pip install -e ".[dev,all]"

# Run tests
pytest

# Type check
mypy src/cmdop_bot

# Lint
ruff check src/cmdop_bot
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | For Telegram |
| `DISCORD_BOT_TOKEN` | Discord bot token | For Discord |
| `SLACK_BOT_TOKEN` | Slack bot token (xoxb-...) | For Slack |
| `SLACK_APP_TOKEN` | Slack app token (xapp-...) | For Slack |
| `CMDOP_API_KEY` | CMDOP API key (cmd_xxx) | Yes |
| `CMDOP_MACHINE` | Default target machine | No |
| `ALLOWED_USERS` | Comma-separated user IDs | No |

## Examples

See the `examples/` directory:
- `telegram_bot.py` - Full Telegram bot example
- `discord_bot.py` - Full Discord bot example
- `slack_app.py` - Full Slack app example
- `multi_channel.py` - Multi-channel hub example

## License

MIT
