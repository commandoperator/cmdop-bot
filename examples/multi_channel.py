#!/usr/bin/env python3
"""Example multi-channel bot with CMDOP integration.

Run Telegram, Discord, and Slack bots simultaneously.

Prerequisites:
    1. Set up credentials for each channel you want to use
    2. Get your CMDOP API key from https://cmdop.com
    3. Install dependencies: pip install cmdop-sdk[all]

Usage:
    export CMDOP_API_KEY="cmd_xxx"
    export TELEGRAM_BOT_TOKEN="123:ABC"  # Optional
    export DISCORD_BOT_TOKEN="xxx"        # Optional
    export SLACK_BOT_TOKEN="xoxb-xxx"     # Optional
    export SLACK_APP_TOKEN="xapp-xxx"     # Optional
    python multi_channel.py
"""

import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Get CMDOP API key (required)
    cmdop_api_key = os.getenv("CMDOP_API_KEY")
    if not cmdop_api_key:
        print("Error: CMDOP_API_KEY environment variable not set")
        sys.exit(1)

    # Optional: target machine
    machine = os.getenv("CMDOP_MACHINE")

    # Import hub
    from cmdop_bot import IntegrationHub

    # Create hub
    hub = IntegrationHub(cmdop_api_key=cmdop_api_key, machine=machine)

    # Add Telegram if configured
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token:
        from cmdop_bot.channels.telegram import TelegramBot

        allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USERS", "")
        allowed_users = None
        if allowed_users_str:
            allowed_users = [int(uid.strip()) for uid in allowed_users_str.split(",")]

        hub.add_channel(TelegramBot(
            token=telegram_token,
            cmdop_api_key=cmdop_api_key,
            allowed_users=allowed_users,
            machine=machine,
        ))
        logger.info("Telegram channel configured")

    # Add Discord if configured
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if discord_token:
        from cmdop_bot.channels.discord import DiscordBot

        guild_ids_str = os.getenv("DISCORD_GUILD_IDS", "")
        guild_ids = None
        if guild_ids_str:
            guild_ids = [int(gid.strip()) for gid in guild_ids_str.split(",")]

        hub.add_channel(DiscordBot(
            token=discord_token,
            cmdop_api_key=cmdop_api_key,
            guild_ids=guild_ids,
            machine=machine,
        ))
        logger.info("Discord channel configured")

    # Add Slack if configured
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
    slack_app_token = os.getenv("SLACK_APP_TOKEN")
    if slack_bot_token and slack_app_token:
        from cmdop_bot.channels.slack import SlackApp

        hub.add_channel(SlackApp(
            bot_token=slack_bot_token,
            app_token=slack_app_token,
            cmdop_api_key=cmdop_api_key,
            machine=machine,
        ))
        logger.info("Slack channel configured")

    # Check if any channels were added
    if not hub.channels:
        print("Error: No channels configured. Set at least one of:")
        print("  - TELEGRAM_BOT_TOKEN")
        print("  - DISCORD_BOT_TOKEN")
        print("  - SLACK_BOT_TOKEN + SLACK_APP_TOKEN")
        sys.exit(1)

    logger.info(f"Starting {len(hub.channels)} channel(s)...")
    logger.info(f"Target machine: {machine or '(default)'}")

    # Run hub
    try:
        async with hub:
            # Run forever
            await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
