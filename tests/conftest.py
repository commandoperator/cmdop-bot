"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def cmdop_api_key() -> str:
    """Fixture for test CMDOP API key."""
    return "cmd_test_key"


@pytest.fixture
def telegram_token() -> str:
    """Fixture for test Telegram token."""
    return "123456:ABC-DEF"


@pytest.fixture
def discord_token() -> str:
    """Fixture for test Discord token."""
    return "test_discord_token"


@pytest.fixture
def slack_bot_token() -> str:
    """Fixture for test Slack bot token."""
    return "xoxb-test-token"


@pytest.fixture
def slack_app_token() -> str:
    """Fixture for test Slack app token."""
    return "xapp-test-token"
