"""Tests for exceptions."""

import pytest

from cmdop_bot.exceptions import (
    IntegrationError,
    ChannelError,
    PermissionDeniedError,
    ConfigurationError,
    RateLimitError,
)


class TestExceptions:
    """Tests for exception classes."""

    def test_integration_error(self):
        """Test base IntegrationError."""
        err = IntegrationError("Test error")
        assert "Test error" in str(err)
        assert err.error_code == "INTEGRATION_ERROR"

    def test_integration_error_with_code(self):
        """Test IntegrationError with custom code."""
        err = IntegrationError("Test", error_code="CUSTOM_CODE")
        assert err.error_code == "CUSTOM_CODE"

    def test_integration_error_with_suggestion(self):
        """Test IntegrationError with suggestion."""
        err = IntegrationError("Test", suggestion="Try this instead")
        assert err.suggestion == "Try this instead"
        assert "Suggestion" in str(err)

    def test_channel_error(self):
        """Test ChannelError."""
        err = ChannelError("Channel failed", channel="telegram")
        assert err.channel == "telegram"
        assert "CHANNEL_ERROR_TELEGRAM" in err.error_code

    def test_permission_denied_error(self):
        """Test PermissionDeniedError."""
        err = PermissionDeniedError(user_id="user123", action="shell")
        assert err.error_code == "PERMISSION_DENIED"
        assert err.user_id == "user123"
        assert err.action == "shell"

    def test_configuration_error(self):
        """Test ConfigurationError."""
        err = ConfigurationError("Invalid config", config_key="api_key")
        assert err.error_code == "CONFIGURATION_ERROR"
        assert err.config_key == "api_key"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        err = RateLimitError(channel="telegram", retry_after=30)
        assert err.retry_after == 30
        assert err.error_code == "RATE_LIMIT"
        assert err.channel == "telegram"

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        assert issubclass(ChannelError, IntegrationError)
        assert issubclass(PermissionDeniedError, IntegrationError)
        assert issubclass(ConfigurationError, IntegrationError)
        assert issubclass(RateLimitError, IntegrationError)
