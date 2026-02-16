"""CMDOP SDK - Multi-channel bot integrations for remote machine access.

Simple, reliable integrations for Telegram, Discord, Slack.

Quick Start (Telegram):
    >>> from cmdop_bot.channels.telegram import TelegramBot
    >>> bot = TelegramBot(token="...", cmdop_api_key="...")
    >>> bot.run()

Quick Start (Discord):
    >>> from cmdop_bot.channels.discord import DiscordBot
    >>> bot = DiscordBot(token="...", cmdop_api_key="...")
    >>> bot.run()
"""

from cmdop_bot._version import __version__

# Exceptions
from cmdop_bot.exceptions import (
    IntegrationError,
    ChannelError,
    PermissionDeniedError,
    ConfigurationError,
)

# Models
from cmdop_bot.models import (
    User,
    Message,
    Command,
    Permission,
    PermissionLevel,
)

# Core
from cmdop_bot.core import (
    BaseChannel,
    MessageHandler,
    PermissionManager,
)

# Hub
from cmdop_bot.hub import (
    IntegrationHub,
    telegram_bot,
    discord_bot,
    slack_app,
)

__all__ = [
    # Version
    "__version__",
    # Exceptions
    "IntegrationError",
    "ChannelError",
    "PermissionDeniedError",
    "ConfigurationError",
    # Models
    "User",
    "Message",
    "Command",
    "Permission",
    "PermissionLevel",
    # Core
    "BaseChannel",
    "MessageHandler",
    "PermissionManager",
    # Hub
    "IntegrationHub",
    "telegram_bot",
    "discord_bot",
    "slack_app",
]
