#!/usr/bin/env python3
"""Example Slack app with CMDOP integration.

Prerequisites:
    1. Create a Slack app at https://api.slack.com/apps
    2. Enable Socket Mode and get an app-level token (xapp-...)
    3. Add a bot user and get the bot token (xoxb-...)
    4. Create a slash command /cmdop
    5. Get your CMDOP API key from https://cmdop.com
    6. Install dependencies: pip install cmdop-sdk[slack]

Usage:
    export SLACK_BOT_TOKEN="xoxb-YOUR-BOT-TOKEN"
    export SLACK_APP_TOKEN="xapp-YOUR-APP-TOKEN"
    export CMDOP_API_KEY="cmd_xxx"
    python slack_app.py
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
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
    slack_app_token = os.getenv("SLACK_APP_TOKEN")
    cmdop_api_key = os.getenv("CMDOP_API_KEY")

    if not slack_bot_token:
        print("Error: SLACK_BOT_TOKEN environment variable not set")
        sys.exit(1)

    if not slack_app_token:
        print("Error: SLACK_APP_TOKEN environment variable not set")
        sys.exit(1)

    if not cmdop_api_key:
        print("Error: CMDOP_API_KEY environment variable not set")
        sys.exit(1)

    # Optional: Get allowed user IDs
    allowed_users_str = os.getenv("ALLOWED_USERS", "")
    allowed_users = None
    if allowed_users_str:
        allowed_users = [uid.strip() for uid in allowed_users_str.split(",")]

    # Optional: Get target machine
    machine = os.getenv("CMDOP_MACHINE")

    # Import here to fail fast if slack-bolt not installed
    try:
        from cmdop_bot.channels.slack import SlackApp
    except ImportError:
        print("Error: slack-bolt not installed. Run: pip install cmdop-sdk[slack]")
        sys.exit(1)

    # Create and run app
    app = SlackApp(
        bot_token=slack_bot_token,
        app_token=slack_app_token,
        cmdop_api_key=cmdop_api_key,
        allowed_users=allowed_users,
        machine=machine,
        timeout=60.0,
    )

    logger.info("Starting CMDOP Slack app...")
    logger.info(f"Target machine: {machine or '(default)'}")
    if allowed_users:
        logger.info(f"Allowed users: {allowed_users}")

    # Run app
    app.run()


if __name__ == "__main__":
    main()
