#!/usr/bin/env python3
"""Example Telegram bot with CMDOP integration.

Prerequisites:
    1. Create a Telegram bot via @BotFather and get the token
    2. Get your CMDOP API key from https://cmdop.com
    3. Install dependencies: pip install cmdop-sdk[telegram]

Usage:
    export TELEGRAM_BOT_TOKEN="123:ABC"
    export CMDOP_API_KEY="cmd_xxx"
    python telegram_bot.py
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
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    cmdop_api_key = os.getenv("CMDOP_API_KEY")

    if not telegram_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)

    if not cmdop_api_key:
        print("Error: CMDOP_API_KEY environment variable not set")
        sys.exit(1)

    # Optional: Get allowed user IDs from environment
    allowed_users_str = os.getenv("ALLOWED_USERS", "")
    allowed_users = None
    if allowed_users_str:
        allowed_users = [int(uid.strip()) for uid in allowed_users_str.split(",")]

    # Optional: Get target machine hostname
    machine = os.getenv("CMDOP_MACHINE")

    # Import here to fail fast if aiogram not installed
    try:
        from cmdop_bot.channels.telegram import TelegramBot
    except ImportError:
        print("Error: aiogram not installed. Run: pip install cmdop-sdk[telegram]")
        sys.exit(1)

    # Create and run bot
    bot = TelegramBot(
        token=telegram_token,
        cmdop_api_key=cmdop_api_key,
        allowed_users=allowed_users,
        machine=machine,
        timeout=60.0,  # Increase timeout for slow commands
    )

    logger.info("Starting CMDOP Telegram bot...")
    logger.info(f"Target machine: {machine or '(default)'}")
    if allowed_users:
        logger.info(f"Allowed users: {allowed_users}")
    else:
        logger.info("Warning: No user restrictions set (all users allowed)")

    # Run bot
    bot.run()


if __name__ == "__main__":
    main()
