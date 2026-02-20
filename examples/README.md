# CMDOP Bot Examples

Simple examples for each platform.

## Prerequisites

1. Download agent from [cmdop.com/downloads](https://cmdop.com/downloads/)
2. Install and authorize the agent on your machine
3. Get API key from [my.cmdop.com/dashboard/settings](https://my.cmdop.com/dashboard/settings/)

## Install

```bash
pip install "cmdop-bot[telegram]"  # or [discord], [slack], [all]
```

## Telegram

```python
from cmdop_bot import Model
from cmdop_bot.channels.telegram import TelegramBot

bot = TelegramBot(
    token="YOUR_TOKEN",
    cmdop_api_key="cmdop_xxx",
    machine="my-server",
    model=Model.balanced(),
)
bot.run()
```

## Discord

```python
from cmdop_bot import Model
from cmdop_bot.channels.discord import DiscordBot

bot = DiscordBot(
    token="YOUR_TOKEN",
    cmdop_api_key="cmdop_xxx",
    machine="my-server",
    model=Model.balanced(),
)
bot.run()
```

## Slack

```python
from cmdop_bot import Model
from cmdop_bot.channels.slack import SlackApp

app = SlackApp(
    bot_token="xoxb-...",
    app_token="xapp-...",
    cmdop_api_key="cmdop_xxx",
    machine="my-server",
    model=Model.balanced(),
)
app.run()
```

## Using CMDOPHandler Directly

```python
from cmdop_bot import CMDOPHandler, Model

async with CMDOPHandler(
    api_key="cmdop_xxx",
    machine="my-server",
    model=Model.balanced(),
) as cmdop:
    result = await cmdop.run_agent("Check disk space")
    print(result.text)
```

## Model Tiers

```python
Model.cheap()      # Most economical
Model.budget()     # Budget-friendly
Model.fast()       # Fastest response
Model.balanced()   # Best value (recommended)
Model.standard()   # Standard
Model.smart()      # Highest quality
Model.premium()    # Premium tier
```
