"""Tests for CMDOPHandler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cmdop_bot import CMDOPHandler, Model, DEFAULT_MODEL


class TestModel:
    """Tests for Model class."""

    def test_cheap(self):
        """Test cheap model alias."""
        assert Model.cheap() == "@cheap+agents"

    def test_budget(self):
        """Test budget model alias."""
        assert Model.budget() == "@budget+agents"

    def test_fast(self):
        """Test fast model alias."""
        assert Model.fast() == "@fast+agents"

    def test_standard(self):
        """Test standard model alias."""
        assert Model.standard() == "@standard+agents"

    def test_balanced(self):
        """Test balanced model alias."""
        assert Model.balanced() == "@balanced+agents"

    def test_smart(self):
        """Test smart model alias."""
        assert Model.smart() == "@smart+agents"

    def test_premium(self):
        """Test premium model alias."""
        assert Model.premium() == "@premium+agents"

    def test_with_vision(self):
        """Test model with vision modifier."""
        assert Model.smart(vision=True) == "@smart+agents+vision"
        assert Model.cheap(vision=True) == "@cheap+agents+vision"

    def test_with_code(self):
        """Test model with code modifier."""
        assert Model.balanced(code=True) == "@balanced+agents+code"

    def test_with_multiple_modifiers(self):
        """Test model with multiple modifiers."""
        assert Model.smart(vision=True, code=True) == "@smart+agents+vision+code"

    def test_default_model(self):
        """Test default model constant."""
        assert DEFAULT_MODEL == "@balanced+agents"


class TestCMDOPHandler:
    """Tests for CMDOPHandler."""

    def test_init(self, cmdop_api_key):
        """Test handler initialization."""
        handler = CMDOPHandler(
            api_key=cmdop_api_key,
            machine="test-server",
            model=Model.cheap(),
        )
        assert handler.machine == "test-server"
        assert handler.model == "@cheap+agents"

    def test_init_defaults(self, cmdop_api_key):
        """Test handler with default values."""
        handler = CMDOPHandler(api_key=cmdop_api_key)
        assert handler.machine is None
        assert handler.model is None

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self, cmdop_api_key):
        """Test get_client creates AsyncCMDOPClient."""
        # Need to specify machine to avoid list_sessions call
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.remote.return_value = mock_client

            client = await handler.get_client()

            mock_client_class.remote.assert_called_once_with(api_key=cmdop_api_key)
            assert client == mock_client

    @pytest.mark.asyncio
    async def test_get_client_sets_machine(self, cmdop_api_key):
        """Test get_client sets machine on all services."""
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="my-server")

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.terminal.set_machine = AsyncMock()
            mock_client.files.set_machine = AsyncMock()
            mock_client.agent.set_machine = AsyncMock()
            mock_client_class.remote.return_value = mock_client

            await handler.get_client()

            mock_client.terminal.set_machine.assert_called_once_with("my-server")
            mock_client.files.set_machine.assert_called_once_with("my-server")
            mock_client.agent.set_machine.assert_called_once_with("my-server")

    @pytest.mark.asyncio
    async def test_run_agent(self, cmdop_api_key):
        """Test run_agent calls client.agent.run."""
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server", model=Model.smart())

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.text = "Agent response"

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.agent.run = AsyncMock(return_value=mock_result)
            mock_client_class.remote.return_value = mock_client

            with patch("cmdop.models.agent.AgentRunOptions") as mock_options_class:
                mock_options = MagicMock()
                mock_options_class.return_value = mock_options

                result = await handler.run_agent("List files")

                mock_client.agent.run.assert_called_once()
                call_args = mock_client.agent.run.call_args
                assert call_args[0][0] == "List files"
                assert result.text == "Agent response"

    @pytest.mark.asyncio
    async def test_execute_shell(self, cmdop_api_key):
        """Test execute_shell calls client.terminal.execute."""
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.terminal.execute = AsyncMock(return_value=(b"output", 0))
            mock_client_class.remote.return_value = mock_client

            output, exit_code = await handler.execute_shell("ls -la", timeout=10.0)

            mock_client.terminal.execute.assert_called_once_with("ls -la", timeout=10.0)
            assert output == b"output"
            assert exit_code == 0

    @pytest.mark.asyncio
    async def test_list_files(self, cmdop_api_key):
        """Test list_files calls client.files.list."""
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")

        mock_response = MagicMock()
        mock_response.entries = []

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.files.list = AsyncMock(return_value=mock_response)
            mock_client_class.remote.return_value = mock_client

            result = await handler.list_files("/tmp")

            mock_client.files.list.assert_called_once_with("/tmp")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_read_file(self, cmdop_api_key):
        """Test read_file calls client.files.read."""
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.files.read = AsyncMock(return_value=b"file content")
            mock_client_class.remote.return_value = mock_client

            content = await handler.read_file("/etc/hostname")

            mock_client.files.read.assert_called_once_with("/etc/hostname")
            assert content == b"file content"

    @pytest.mark.asyncio
    async def test_set_machine(self, cmdop_api_key):
        """Test set_machine updates all services."""
        # Start with a machine to avoid list_sessions error
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="initial-server")

        mock_session = MagicMock()
        mock_session.machine_hostname = "full-hostname.local"

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.terminal.set_machine = AsyncMock(return_value=mock_session)
            mock_client.files.set_machine = AsyncMock()
            mock_client.agent.set_machine = AsyncMock()
            mock_client_class.remote.return_value = mock_client

            result = await handler.set_machine("full-hostname")

            assert result == "full-hostname.local"
            assert handler.machine == "full-hostname.local"

    @pytest.mark.asyncio
    async def test_close(self, cmdop_api_key):
        """Test close cleans up client."""
        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")

        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.remote.return_value = mock_client

            await handler.get_client()  # Initialize client
            await handler.close()

            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, cmdop_api_key):
        """Test async context manager."""
        with patch("cmdop.AsyncCMDOPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.remote.return_value = mock_client

            async with CMDOPHandler(api_key=cmdop_api_key, machine="test-server") as handler:
                await handler.get_client()

            mock_client.close.assert_called_once()
