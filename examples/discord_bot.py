#!/usr/bin/env python3
"""Example Discord bot with CMDOP integration.

Prerequisites:
    1. Create a Discord application at https://discord.com/developers
    2. Create a bot and get the token
    3. Enable "applications.commands" scope when adding to server
    4. Get your CMDOP API key from https://cmdop.com
    5. Install dependencies: pip install cmdop-sdk[discord]

Usage:
    export DISCORD_BOT_TOKEN="YOUR_TOKEN"
    export CMDOP_API_KEY="cmd_xxx"
    python discord_bot.py
"""

import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    # Get credentials from environment
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    cmdop_api_key = os.getenv("CMDOP_API_KEY")

    if not discord_token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set")
        sys.exit(1)

    if not cmdop_api_key:
        print("Error: CMDOP_API_KEY environment variable not set")
        sys.exit(1)

    # Optional: Get guild IDs for faster command sync (development)
    guild_ids_str = os.getenv("DISCORD_GUILD_IDS", "")
    guild_ids = None
    if guild_ids_str:
        guild_ids = [int(gid.strip()) for gid in guild_ids_str.split(",")]

    # Optional: Get allowed user IDs
    allowed_users_str = os.getenv("ALLOWED_USERS", "")
    allowed_users = None
    if allowed_users_str:
        allowed_users = [int(uid.strip()) for uid in allowed_users_str.split(",")]

    # Optional: Get target machine
    machine = os.getenv("CMDOP_MACHINE")

    # Import here to fail fast if discord.py not installed
    try:
        from cmdop_bot.channels.discord import DiscordBot
    except ImportError:
        print("Error: discord.py not installed. Run: pip install cmdop-sdk[discord]")
        sys.exit(1)

    # Create and run bot
    bot = DiscordBot(
        token=discord_token,
        cmdop_api_key=cmdop_api_key,
        guild_ids=guild_ids,
        allowed_users=allowed_users,
        machine=machine,
        timeout=60.0,
    )

    logger.info("Starting CMDOP Discord bot...")
    logger.info(f"Target machine: {machine or '(default)'}")
    if guild_ids:
        logger.info(f"Guild IDs: {guild_ids}")
    if allowed_users:
        logger.info(f"Allowed users: {allowed_users}")

    # Run bot
    bot.run()


if __name__ == "__main__":
    main()
