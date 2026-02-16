"""Exception type definitions."""

from typing import Any


class IntegrationError(Exception):
    """Base exception for all SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "INTEGRATION_ERROR",
        suggestion: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.suggestion = suggestion
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        parts = [f"[{self.error_code}] {self.message}"]
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return " | ".join(parts)


class ChannelError(IntegrationError):
    """Error from a specific channel (Telegram, Discord, etc.)."""

    def __init__(
        self,
        message: str,
        channel: str,
        *,
        suggestion: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code=f"CHANNEL_ERROR_{channel.upper()}",
            suggestion=suggestion,
            details={"channel": channel, **(details or {})},
        )
        self.channel = channel


class PermissionDeniedError(IntegrationError):
    """User does not have permission for the requested action."""

    def __init__(
        self,
        user_id: str,
        action: str,
        *,
        machine: str | None = None,
    ) -> None:
        super().__init__(
            f"Permission denied: {action}",
            error_code="PERMISSION_DENIED",
            suggestion="Contact administrator for access",
            details={"user_id": user_id, "action": action, "machine": machine},
        )
        self.user_id = user_id
        self.action = action
        self.machine = machine


class ConfigurationError(IntegrationError):
    """Invalid or missing configuration."""

    def __init__(
        self,
        message: str,
        config_key: str,
        *,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            suggestion=suggestion or f"Check the '{config_key}' configuration",
            details={"config_key": config_key},
        )
        self.config_key = config_key


class RateLimitError(IntegrationError):
    """Rate limit exceeded."""

    def __init__(
        self,
        channel: str,
        retry_after: int | None = None,
    ) -> None:
        suggestion = f"Retry after {retry_after}s" if retry_after else "Wait before retrying"
        super().__init__(
            "Rate limit exceeded",
            error_code="RATE_LIMIT",
            suggestion=suggestion,
            details={"channel": channel, "retry_after": retry_after},
        )
        self.channel = channel
        self.retry_after = retry_after


class ConnectionError(IntegrationError):
    """Failed to connect to CMDOP or channel API."""

    def __init__(
        self,
        message: str,
        service: str,
        *,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="CONNECTION_ERROR",
            suggestion="Check network connectivity and credentials",
            details={"service": service},
        )
        self.service = service
        self.original_error = original_error
