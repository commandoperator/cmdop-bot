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

With custom model:
    >>> from cmdop_bot import Model
    >>> bot = TelegramBot(
    ...     token="...",
    ...     cmdop_api_key="...",
    ...     model=Model.balanced(),  # or Model.cheap(), Model.smart()
    ... )
"""

from cmdop_bot._version import __version__


class Model:
    """Model tier aliases for SDKRouter.

    Uses SDKRouter's dynamic model routing - the actual model is resolved
    server-side based on current best options for each tier.

    Examples:
        >>> bot = TelegramBot(..., model=Model.cheap())
        >>> bot = TelegramBot(..., model=Model.smart())
        >>> bot = TelegramBot(..., model=Model.balanced(vision=True))
    """

    @staticmethod
    def cheap(*, vision: bool = False, code: bool = False) -> str:
        """Cheapest available model."""
        return _build_alias("cheap", vision=vision, code=code)

    @staticmethod
    def budget(*, vision: bool = False, code: bool = False) -> str:
        """Budget-friendly model."""
        return _build_alias("budget", vision=vision, code=code)

    @staticmethod
    def fast(*, vision: bool = False, code: bool = False) -> str:
        """Fastest response time."""
        return _build_alias("fast", vision=vision, code=code)

    @staticmethod
    def standard(*, vision: bool = False, code: bool = False) -> str:
        """Standard performance."""
        return _build_alias("standard", vision=vision, code=code)

    @staticmethod
    def balanced(*, vision: bool = False, code: bool = False) -> str:
        """Best quality/price ratio (recommended)."""
        return _build_alias("balanced", vision=vision, code=code)

    @staticmethod
    def smart(*, vision: bool = False, code: bool = False) -> str:
        """Highest quality model."""
        return _build_alias("smart", vision=vision, code=code)

    @staticmethod
    def premium(*, vision: bool = False, code: bool = False) -> str:
        """Premium tier model."""
        return _build_alias("premium", vision=vision, code=code)


def _build_alias(tier: str, *, vision: bool = False, code: bool = False) -> str:
    """Build model alias with optional modifiers."""
    parts = [f"@{tier}", "agents"]  # Always add +agents for CMDOP
    if vision:
        parts.append("vision")
    if code:
        parts.append("code")
    return "+".join(parts)


# Default model for CMDOP agents
DEFAULT_MODEL = "@balanced+agents"

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
    CMDOPHandler,
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
    # Model aliases
    "Model",
    "DEFAULT_MODEL",
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
    "CMDOPHandler",
    "MessageHandler",
    "PermissionManager",
    # Hub
    "IntegrationHub",
    "telegram_bot",
    "discord_bot",
    "slack_app",
]
