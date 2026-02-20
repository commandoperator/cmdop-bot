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
from cmdop_bot import Model
from cmdop_bot.channels.telegram import TelegramBot

bot = TelegramBot(
    token="YOUR_TELEGRAM_BOT_TOKEN",
    cmdop_api_key="YOUR_CMDOP_API_KEY",
    allowed_users=[123456789],  # Your Telegram user ID
    machine="my-server",        # Optional: target machine
    model=Model.balanced(),     # Optional: AI model tier
)

bot.run()
```

### Discord Bot

```python
from cmdop_bot.channels.discord import DiscordBot

bot = DiscordBot(
    token="YOUR_DISCORD_BOT_TOKEN",
    cmdop_api_key="YOUR_CMDOP_API_KEY",
    guild_ids=[123456789],  # Optional: for faster command sync
)

bot.run()
```

### Slack App

```python
from cmdop_bot.channels.slack import SlackApp

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

## CMDOPHandler

Use `CMDOPHandler` directly in your own bot:

```python
from cmdop_bot import CMDOPHandler, Model

# Create handler with all CMDOP logic
async with CMDOPHandler(
    api_key="cmd_xxx",
    machine="my-server",
    model=Model.balanced(),
) as cmdop:
    # Run AI agent
    result = await cmdop.run_agent("List files in /tmp")
    print(result.text)

    # Execute shell command
    output, exit_code = await cmdop.execute_shell("ls -la")
    print(output.decode())

    # List files
    files = await cmdop.list_files("/var/log")
    for f in files.entries:
        print(f.name)

    # Read file
    content = await cmdop.read_file("/etc/hostname")
    print(content.decode())

    # Switch machine
    await cmdop.set_machine("other-server")
```

## Permissions

Control who can use your bot:

```python
from cmdop_bot import PermissionManager, PermissionLevel

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

## Model Selection

Choose AI model tier for `/agent` command:

```python
from cmdop_bot import Model

# Available tiers (cheapest to most capable)
Model.cheap()      # "@cheap+agents"    - Most economical
Model.budget()     # "@budget+agents"   - Budget-friendly
Model.fast()       # "@fast+agents"     - Fastest response
Model.standard()   # "@standard+agents" - Standard performance
Model.balanced()   # "@balanced+agents" - Best value (default)
Model.smart()      # "@smart+agents"    - Highest quality
Model.premium()    # "@premium+agents"  - Premium tier

# With capabilities
Model.smart(vision=True)   # "@smart+agents+vision"
Model.balanced(code=True)  # "@balanced+agents+code"

# Use in bot
bot = TelegramBot(
    token="...",
    cmdop_api_key="...",
    model=Model.cheap(),  # Use cheapest model
)
```

Models are resolved dynamically by SDKRouter - the actual LLM is selected server-side based on current best options for each tier.

## Architecture

```
+--------------+
|  Telegram    |
|  Discord     |---> CMDOPHandler ---> CMDOP SDK ---> Your Servers
|  Slack       |
+--------------+
```

All bots share the same `CMDOPHandler` class which encapsulates:
- CMDOP client initialization and connection management
- Machine targeting (switch between servers)
- Model selection (AI tier for agent commands)
- Shell command execution
- File operations (list, read)
- AI agent execution

- **Simple**: Each bot uses CMDOPHandler for all CMDOP logic
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
| `CMDOP_MODEL` | Model tier (@cheap, @balanced, @smart) | No |
| `ALLOWED_USERS` | Comma-separated user IDs | No |

## License

MIT
