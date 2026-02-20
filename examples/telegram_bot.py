#!/usr/bin/env python3
"""Telegram bot with CMDOP integration.

Prerequisites:
    1. Create bot via @BotFather, get token
    2. Get CMDOP API key from https://my.cmdop.com/dashboard/settings/
    3. pip install "cmdop-bot[telegram]"

Usage:
    python telegram_bot.py
"""

from cmdop_bot import Model
from cmdop_bot.channels.telegram import TelegramBot

bot = TelegramBot(
    token="YOUR_TELEGRAM_BOT_TOKEN",
    cmdop_api_key="cmdop_xxx",  # https://my.cmdop.com/dashboard/settings/
    allowed_users=[123456789],  # Your Telegram user ID
    machine="my-server",        # Target machine hostname
    model=Model.balanced(),     # Model tier
)

bot.run()
