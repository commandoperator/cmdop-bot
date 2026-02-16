"""Tests for command handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cmdop_bot.models import User, Message, Command
from cmdop_bot.handlers import ShellHandler, AgentHandler, HelpHandler, FilesHandler, LsHandler, CatHandler


@pytest.fixture
def mock_cmdop_client():
    """Mock CMDOP client."""
    client = AsyncMock()
    client.terminal.execute = AsyncMock(return_value=(b"output", 0))
    client.terminal.set_machine = AsyncMock()
    client.agent.run = AsyncMock(return_value=MagicMock(
        success=True,
        text="Agent completed",
        error=None,
    ))

    # Mock file operations
    mock_entry = MagicMock()
    mock_entry.name = "test.txt"
    mock_entry.type = MagicMock(value="file")
    mock_entry.size = 1024

    mock_list_response = MagicMock()
    mock_list_response.entries = [mock_entry]

    client.files.list = AsyncMock(return_value=mock_list_response)
    client.files.read = AsyncMock(return_value=b"file content")

    mock_info = MagicMock()
    mock_info.path = "/test/file.txt"
    mock_info.type = MagicMock(value="file")
    mock_info.size = 1024
    mock_info.modified_at = None
    mock_info.permissions = "rw-r--r--"
    client.files.info = AsyncMock(return_value=mock_info)

    return client


@pytest.fixture
def sample_command():
    """Create sample command."""
    user = User(id="123", channel="telegram")
    msg = Message(
        id="msg1",
        channel="telegram",
        chat_id="chat1",
        user=user,
        text="/shell ls -la",
    )
    return Command(
        name="shell",
        args=["ls", "-la"],
        raw_text="/shell ls -la",
        message=msg,
    )


class TestShellHandler:
    """Tests for ShellHandler."""

    @pytest.mark.asyncio
    async def test_handle_empty_args(self, cmdop_api_key):
        """Test handler with empty arguments."""
        handler = ShellHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/shell",
        )
        cmd = Command(name="shell", args=[], raw_text="/shell", message=msg)

        await handler.handle(cmd, send)

        send.assert_called_once()
        assert "Usage" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_success(self, cmdop_api_key, sample_command, mock_cmdop_client):
        """Test successful command execution."""
        handler = ShellHandler(cmdop_api_key)
        send = AsyncMock()

        with patch.object(handler, '_get_client', return_value=mock_cmdop_client):
            await handler.handle(sample_command, send)

        send.assert_called_once()
        assert "```" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_error(self, cmdop_api_key, sample_command, mock_cmdop_client):
        """Test error handling."""
        handler = ShellHandler(cmdop_api_key)
        send = AsyncMock()

        mock_cmdop_client.terminal.execute = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        with patch.object(handler, '_get_client', return_value=mock_cmdop_client):
            await handler.handle(sample_command, send)

        send.assert_called_once()
        assert "Error" in send.call_args[0][0]


class TestAgentHandler:
    """Tests for AgentHandler."""

    @pytest.mark.asyncio
    async def test_handle_empty_args(self, cmdop_api_key):
        """Test handler with empty arguments."""
        handler = AgentHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/agent",
        )
        cmd = Command(name="agent", args=[], raw_text="/agent", message=msg)

        await handler.handle(cmd, send)

        send.assert_called_once()
        assert "Usage" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_success(self, cmdop_api_key, mock_cmdop_client):
        """Test successful agent execution."""
        handler = AgentHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/agent List files",
        )
        cmd = Command(
            name="agent",
            args=["List", "files"],
            raw_text="/agent List files",
            message=msg,
        )

        with patch.object(handler, '_get_client', return_value=mock_cmdop_client):
            await handler.handle(cmd, send)

        send.assert_called_once()
        assert "Agent completed" in send.call_args[0][0]


class TestHelpHandler:
    """Tests for HelpHandler."""

    @pytest.mark.asyncio
    async def test_handle_shows_commands(self):
        """Test help shows available commands."""
        shell_handler = MagicMock()
        shell_handler.name = "shell"
        shell_handler.description = "Execute shell command"

        help_handler = HelpHandler(handlers=[shell_handler])
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/help",
        )
        cmd = Command(name="help", args=[], raw_text="/help", message=msg)

        await help_handler.handle(cmd, send)

        send.assert_called_once()
        response = send.call_args[0][0]
        assert "shell" in response
        assert "help" in response

    def test_add_handler(self):
        """Test adding handler to help list."""
        help_handler = HelpHandler()

        mock_handler = MagicMock()
        mock_handler.name = "test"
        mock_handler.description = "Test command"

        help_handler.add_handler(mock_handler)

        assert mock_handler in help_handler._handlers


class TestFilesHandler:
    """Tests for FilesHandler."""

    @pytest.mark.asyncio
    async def test_handle_empty_args(self, cmdop_api_key):
        """Test handler with empty arguments shows usage."""
        handler = FilesHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/files",
        )
        cmd = Command(name="files", args=[], raw_text="/files", message=msg)

        await handler.handle(cmd, send)

        send.assert_called_once()
        assert "Usage" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_ls(self, cmdop_api_key, mock_cmdop_client):
        """Test listing directory."""
        handler = FilesHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/files ls /home",
        )
        cmd = Command(
            name="files",
            args=["ls", "/home"],
            raw_text="/files ls /home",
            message=msg,
        )

        with patch.object(handler, '_get_client', return_value=mock_cmdop_client):
            await handler.handle(cmd, send)

        send.assert_called_once()
        assert "test.txt" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_cat(self, cmdop_api_key, mock_cmdop_client):
        """Test reading file."""
        handler = FilesHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/files cat /home/test.txt",
        )
        cmd = Command(
            name="files",
            args=["cat", "/home/test.txt"],
            raw_text="/files cat /home/test.txt",
            message=msg,
        )

        with patch.object(handler, '_get_client', return_value=mock_cmdop_client):
            await handler.handle(cmd, send)

        send.assert_called_once()
        assert "file content" in send.call_args[0][0]


class TestLsHandler:
    """Tests for LsHandler shortcut."""

    @pytest.mark.asyncio
    async def test_handle_ls_shortcut(self, cmdop_api_key, mock_cmdop_client):
        """Test /ls shortcut."""
        handler = LsHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/ls /home",
        )
        cmd = Command(
            name="ls",
            args=["/home"],
            raw_text="/ls /home",
            message=msg,
        )

        with patch.object(handler._files_handler, '_get_client', return_value=mock_cmdop_client):
            await handler.handle(cmd, send)

        send.assert_called_once()
        assert "test.txt" in send.call_args[0][0]


class TestCatHandler:
    """Tests for CatHandler shortcut."""

    @pytest.mark.asyncio
    async def test_handle_empty_args(self, cmdop_api_key):
        """Test /cat without path shows usage."""
        handler = CatHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/cat",
        )
        cmd = Command(name="cat", args=[], raw_text="/cat", message=msg)

        await handler.handle(cmd, send)

        send.assert_called_once()
        assert "Usage" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_cat_shortcut(self, cmdop_api_key, mock_cmdop_client):
        """Test /cat shortcut."""
        handler = CatHandler(cmdop_api_key)
        send = AsyncMock()

        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/cat /home/test.txt",
        )
        cmd = Command(
            name="cat",
            args=["/home/test.txt"],
            raw_text="/cat /home/test.txt",
            message=msg,
        )

        with patch.object(handler._files_handler, '_get_client', return_value=mock_cmdop_client):
            await handler.handle(cmd, send)

        send.assert_called_once()
        assert "file content" in send.call_args[0][0]
