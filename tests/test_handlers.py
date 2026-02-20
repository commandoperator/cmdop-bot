"""Tests for TelegramBot handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from cmdop_bot.models import User, Message, Command


@pytest.fixture
def mock_cmdop_handler():
    """Mock CMDOPHandler."""
    handler = AsyncMock()
    handler.machine = "test-server"
    handler.model = "@balanced+agents"

    # Mock agent result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.text = "Agent completed the task"
    mock_result.error = None
    handler.run_agent = AsyncMock(return_value=mock_result)

    # Mock shell execution
    handler.execute_shell = AsyncMock(return_value=(b"command output", 0))

    # Mock file operations
    mock_entry = MagicMock()
    mock_entry.name = "test.txt"
    mock_entry.type = MagicMock(value="file")
    mock_entry.size = 1024

    mock_list_response = MagicMock()
    mock_list_response.entries = [mock_entry]
    handler.list_files = AsyncMock(return_value=mock_list_response)

    handler.read_file = AsyncMock(return_value=b"file content here")

    mock_info = MagicMock()
    mock_info.path = "/test/file.txt"
    mock_info.type = MagicMock(value="file")
    mock_info.size = 1024
    mock_info.modified_at = None
    mock_info.permissions = "rw-r--r--"
    handler.file_info = AsyncMock(return_value=mock_info)

    handler.set_machine = AsyncMock(return_value="new-server.local")
    handler.close = AsyncMock()

    return handler


@pytest.fixture
def sample_user():
    """Create sample user."""
    return User(id="123456", channel="telegram", username="testuser")


@pytest.fixture
def sample_message(sample_user):
    """Create sample message."""
    return Message(
        id="msg1",
        channel="telegram",
        chat_id="chat1",
        user=sample_user,
        text="/shell ls -la",
    )


class TestTelegramBotInit:
    """Tests for TelegramBot initialization."""

    def test_init_with_model(self, telegram_token, cmdop_api_key):
        """Test bot initialization with model."""
        from cmdop_bot import Model
        from cmdop_bot.channels.telegram import TelegramBot

        bot = TelegramBot(
            token=telegram_token,
            cmdop_api_key=cmdop_api_key,
            model=Model.cheap(),
        )

        assert bot._cmdop._model == "@cheap+agents"

    def test_init_with_machine(self, telegram_token, cmdop_api_key):
        """Test bot initialization with machine."""
        from cmdop_bot.channels.telegram import TelegramBot

        bot = TelegramBot(
            token=telegram_token,
            cmdop_api_key=cmdop_api_key,
            machine="my-server",
        )

        assert bot._cmdop._machine == "my-server"

    def test_init_with_allowed_users(self, telegram_token, cmdop_api_key):
        """Test bot initialization with allowed users."""
        from cmdop_bot.channels.telegram import TelegramBot

        bot = TelegramBot(
            token=telegram_token,
            cmdop_api_key=cmdop_api_key,
            allowed_users=[123, 456],
        )

        assert bot._allowed_users == {123, 456}

    def test_init_defaults(self, telegram_token, cmdop_api_key):
        """Test bot initialization with defaults."""
        from cmdop_bot.channels.telegram import TelegramBot

        bot = TelegramBot(
            token=telegram_token,
            cmdop_api_key=cmdop_api_key,
        )

        assert bot._allowed_users is None
        assert bot._cmdop._machine is None
        assert bot._cmdop._model is None


class TestCommandParsing:
    """Tests for command parsing."""

    def test_parse_shell_command(self, sample_user):
        """Test parsing shell command."""
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=sample_user,
            text="/shell ls -la /tmp",
        )
        cmd = Command.parse(msg.text, msg)

        assert cmd is not None
        assert cmd.name == "shell"
        assert cmd.args == ["ls", "-la", "/tmp"]
        assert cmd.args_text == "ls -la /tmp"

    def test_parse_agent_command(self, sample_user):
        """Test parsing agent command."""
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=sample_user,
            text="/agent List all files in /home",
        )
        cmd = Command.parse(msg.text, msg)

        assert cmd is not None
        assert cmd.name == "agent"
        assert cmd.args_text == "List all files in /home"

    def test_parse_ls_command(self, sample_user):
        """Test parsing ls command."""
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=sample_user,
            text="/ls /var/log",
        )
        cmd = Command.parse(msg.text, msg)

        assert cmd is not None
        assert cmd.name == "ls"
        assert cmd.args_text == "/var/log"

    def test_parse_machine_command(self, sample_user):
        """Test parsing machine command."""
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=sample_user,
            text="/machine prod-server",
        )
        cmd = Command.parse(msg.text, msg)

        assert cmd is not None
        assert cmd.name == "machine"
        assert cmd.args_text == "prod-server"

    def test_parse_non_command(self):
        """Test parsing non-command returns None."""
        cmd = Command.parse("Hello world")
        assert cmd is None

    def test_parse_empty_args(self, sample_user):
        """Test parsing command without args."""
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=sample_user,
            text="/help",
        )
        cmd = Command.parse(msg.text, msg)

        assert cmd is not None
        assert cmd.name == "help"
        assert cmd.args == []
        assert cmd.args_text == ""


class TestFormatSize:
    """Tests for file size formatting."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        from cmdop_bot.channels.telegram.handlers.files import FilesHandler

        assert FilesHandler._format_size(500) == "500 B"
        assert FilesHandler._format_size(0) == "0 B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        from cmdop_bot.channels.telegram.handlers.files import FilesHandler

        assert FilesHandler._format_size(1024) == "1.0 KB"
        assert FilesHandler._format_size(2048) == "2.0 KB"

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        from cmdop_bot.channels.telegram.handlers.files import FilesHandler

        assert FilesHandler._format_size(1024 * 1024) == "1.0 MB"
        assert FilesHandler._format_size(5 * 1024 * 1024) == "5.0 MB"

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        from cmdop_bot.channels.telegram.handlers.files import FilesHandler

        assert FilesHandler._format_size(1024 * 1024 * 1024) == "1.0 GB"
