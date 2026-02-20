"""CMDOP handler - unified logic for all bot channels."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from cmdop import AsyncCMDOPClient
    from cmdop.models.agent import AgentResult, AgentStreamEvent
    from cmdop.models.files import FileListResponse

logger = logging.getLogger(__name__)


class CMDOPHandler:
    """Base CMDOP logic for all bot channels.

    Handles client initialization, machine targeting, model selection,
    and all CMDOP operations (agent, shell, files).

    Example:
        >>> from cmdop_bot import Model
        >>> from cmdop_bot.core import CMDOPHandler
        >>>
        >>> handler = CMDOPHandler(
        ...     api_key="cmd_xxx",
        ...     machine="my-server",
        ...     model=Model.balanced(),
        ... )
        >>>
        >>> # Use in your bot
        >>> result = await handler.run_agent("List files in /tmp")
        >>> output = await handler.execute_shell("ls -la")
    """

    def __init__(
        self,
        api_key: str,
        *,
        machine: str | None = None,
        model: str | None = None,
        server: str | None = None,
        insecure: bool = False,
    ) -> None:
        """Initialize CMDOP handler.

        Args:
            api_key: CMDOP API key (cmd_xxx format)
            machine: Target machine hostname. None = use default.
            model: Model tier alias (e.g., "@balanced+agents").
                   Use Model.cheap(), Model.balanced(), etc.
            server: gRPC server address (e.g., "127.0.0.1:50051").
                   None = use default (grpc.cmdop.com:443).
            insecure: Use insecure connection (no TLS). Default: False.
        """
        self._api_key = api_key
        self._machine = machine
        self._model = model
        self._server = server
        self._insecure = insecure
        self._client: AsyncCMDOPClient | None = None
        self._initialized = False

    @property
    def machine(self) -> str | None:
        """Current target machine."""
        return self._machine

    @property
    def model(self) -> str | None:
        """Current model alias."""
        return self._model

    async def get_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client with lazy initialization."""
        if self._client is None:
            from cmdop import AsyncCMDOPClient

            self._client = AsyncCMDOPClient.remote(
                api_key=self._api_key,
                server=self._server,
                insecure=self._insecure,
            )
            logger.info(f"Created CMDOP client, machine={self._machine}")

        # Initialize machine if specified but not yet initialized
        if self._machine and not self._initialized:
            try:
                # Set machine for all services
                await self._client.terminal.set_machine(self._machine)
                await self._client.files.set_machine(self._machine)
                await self._client.agent.set_machine(self._machine)
                logger.info(f"Connected to session on: {self._machine}")
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to set machine '{self._machine}': {e}")
                raise

        if not self._initialized:
            logger.warning(
                "No machine specified. Use /machine <hostname> or pass machine= parameter."
            )

        return self._client

    async def set_machine(self, hostname: str) -> str:
        """Set target machine.

        Args:
            hostname: Machine hostname (can be partial match)

        Returns:
            Full hostname of connected machine

        Raises:
            CMDOPError: If machine not found or connection failed
        """
        client = await self.get_client()

        session = await client.terminal.set_machine(hostname)
        await client.files.set_machine(hostname)
        await client.agent.set_machine(hostname)

        self._machine = session.machine_hostname
        logger.info(f"Switched to machine: {self._machine}")

        return self._machine

    async def run_agent(self, prompt: str) -> AgentResult:
        """Run AI agent with prompt.

        Args:
            prompt: Task description for the agent

        Returns:
            AgentResult with response text, tool results, etc.
        """
        from cmdop.models.agent import AgentRunOptions

        client = await self.get_client()

        options = AgentRunOptions(model=self._model) if self._model else None
        result = await client.agent.run(prompt, options=options)

        return result

    async def run_agent_stream(
        self,
        prompt: str,
        on_event: Callable[[AgentStreamEvent], Awaitable[None]] | None = None,
    ) -> AgentResult:
        """Run AI agent with streaming events.

        Args:
            prompt: Task description for the agent
            on_event: Optional callback for each streaming event.
                     Called with AgentStreamEvent for tokens, tool calls, etc.

        Returns:
            AgentResult with final response

        Example:
            >>> async def handle_event(event):
            ...     if event.type == "token":
            ...         print(event.payload, end="", flush=True)
            ...     elif event.type == "tool_start":
            ...         print(f"\\nUsing: {event.payload['tool_name']}")
            >>>
            >>> result = await handler.run_agent_stream(
            ...     "Check disk space",
            ...     on_event=handle_event,
            ... )
        """
        from cmdop.models.agent import AgentRunOptions, AgentResult as AgentResultModel

        client = await self.get_client()

        options = AgentRunOptions(model=self._model) if self._model else None

        result: AgentResultModel | None = None

        async for event in client.agent.run_stream(prompt, options=options):
            if isinstance(event, AgentResultModel):
                # Final result
                result = event
            elif on_event:
                # Streaming event - call callback
                await on_event(event)

        if result is None:
            # Should not happen, but handle gracefully
            from cmdop.models.agent import AgentResult as AR
            result = AR(success=False, text="", error="No result received from agent")

        return result

    async def execute_shell(
        self,
        command: str,
        timeout: float = 30.0,
    ) -> tuple[bytes, int]:
        """Execute shell command.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds

        Returns:
            Tuple of (output_bytes, exit_code)
        """
        client = await self.get_client()
        output, exit_code = await client.terminal.execute(command, timeout=timeout)
        return output, exit_code

    async def list_files(self, path: str = ".") -> FileListResponse:
        """List directory contents.

        Args:
            path: Directory path to list

        Returns:
            FileListResponse with entries
        """
        client = await self.get_client()
        return await client.files.list(path)

    async def read_file(self, path: str) -> bytes:
        """Read file contents.

        Args:
            path: File path to read

        Returns:
            File contents as bytes
        """
        client = await self.get_client()
        return await client.files.read(path)

    async def file_info(self, path: str):
        """Get file info.

        Args:
            path: File path

        Returns:
            FileInfo object
        """
        client = await self.get_client()
        return await client.files.info(path)

    async def close(self) -> None:
        """Close CMDOP client and cleanup resources."""
        if self._client:
            await self._client.close()
            self._client = None
            self._initialized = False
            logger.info("CMDOP handler closed")

    async def __aenter__(self) -> CMDOPHandler:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
