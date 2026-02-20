#!/usr/bin/env python3
"""Slack app with CMDOP integration.

Prerequisites:
    1. Create Slack app at https://api.slack.com/apps
    2. Enable Socket Mode, get app token (xapp-...)
    3. Get bot token (xoxb-...)
    4. Get CMDOP API key from https://cmdop.com
    5. pip install cmdop-bot[slack]

Usage:
    python slack_app.py
"""

from cmdop_bot import Model
from cmdop_bot.channels.slack import SlackApp

app = SlackApp(
    bot_token="xoxb-YOUR-BOT-TOKEN",
    app_token="xapp-YOUR-APP-TOKEN",
    cmdop_api_key="cmdop_xxx",
    machine="my-server",        # Target machine hostname
    model=Model.balanced(),     # Model tier
)

app.run()
