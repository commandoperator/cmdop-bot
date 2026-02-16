"""Exception types for CMDOP SDK."""

from cmdop_bot.exceptions.types import (
    IntegrationError,
    ChannelError,
    PermissionDeniedError,
    ConfigurationError,
    RateLimitError,
    ConnectionError,
)

__all__ = [
    "IntegrationError",
    "ChannelError",
    "PermissionDeniedError",
    "ConfigurationError",
    "RateLimitError",
    "ConnectionError",
]
