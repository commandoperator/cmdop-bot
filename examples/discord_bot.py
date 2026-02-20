#!/usr/bin/env python3
"""Discord bot with CMDOP integration.

Prerequisites:
    1. Create Discord app at https://discord.com/developers
    2. Get bot token
    3. Get CMDOP API key from https://my.cmdop.com/dashboard/settings/
    4. pip install "cmdop-bot[discord]"

Usage:
    python discord_bot.py
"""

from cmdop_bot import Model
from cmdop_bot.channels.discord import DiscordBot

bot = DiscordBot(
    token="YOUR_DISCORD_BOT_TOKEN",
    cmdop_api_key="cmdop_xxx",  # https://my.cmdop.com/dashboard/settings/
    guild_ids=[123456789],      # Your server ID (for faster sync)
    machine="my-server",        # Target machine hostname
    model=Model.balanced(),     # Model tier
)

bot.run()
