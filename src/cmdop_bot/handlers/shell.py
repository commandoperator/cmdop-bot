"""Shell command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.core.handler import MessageHandler, SendCallback
from cmdop_bot.models import Command

if TYPE_CHECKING:
    from cmdop import AsyncCMDOPClient

logger = logging.getLogger(__name__)


class ShellHandler(MessageHandler):
    """Handle /shell command - execute shell commands via CMDOP.

    Example:
        >>> handler = ShellHandler(cmdop_api_key="cmd_xxx")
        >>> await handler.handle(command, send)
    """

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize handler.

        Args:
            cmdop_api_key: CMDOP API key (cmd_xxx format)
            machine: Target machine hostname. None = use default.
            timeout: Command execution timeout in seconds.
        """
        self._api_key = cmdop_api_key
        self._machine = machine
        self._timeout = timeout
        self._client: AsyncCMDOPClient | None = None

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute shell command on remote machine"

    async def _get_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client."""
        if self._client is None:
            from cmdop import AsyncCMDOPClient

            self._client = AsyncCMDOPClient.remote(api_key=self._api_key)

            if self._machine:
                await self._client.terminal.set_machine(self._machine)

        return self._client

    async def handle(self, command: Command, send: SendCallback) -> None:
        """Execute shell command via CMDOP."""
        if not command.args_text:
            await send("Usage: /shell <command>")
            return

        try:
            client = await self._get_client()

            output, exit_code = await client.terminal.execute(
                command.args_text,
                timeout=self._timeout,
            )

            # Format output
            output_text = output.decode("utf-8", errors="replace")

            if exit_code == 0:
                result = f"```\n{output_text}\n```"
            elif exit_code == -1:
                result = f"Command timed out or failed:\n```\n{output_text}\n```"
            else:
                result = f"Exit code {exit_code}:\n```\n{output_text}\n```"

            await send(result)

        except Exception as e:
            logger.exception("Shell command failed")
            await send(f"Error: {e}")

    async def close(self) -> None:
        """Close CMDOP client."""
        if self._client is not None:
            await self._client.close()
            self._client = None
