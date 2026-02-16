"""AI Agent command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.core.handler import MessageHandler, SendCallback
from cmdop_bot.models import Command

if TYPE_CHECKING:
    from cmdop import AsyncCMDOPClient

logger = logging.getLogger(__name__)


class AgentHandler(MessageHandler):
    """Handle /agent command - run AI agent tasks via CMDOP.

    Example:
        >>> handler = AgentHandler(cmdop_api_key="cmd_xxx")
        >>> await handler.handle(command, send)
    """

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
    ) -> None:
        """Initialize handler.

        Args:
            cmdop_api_key: CMDOP API key (cmd_xxx format)
            machine: Target machine hostname. None = use default.
        """
        self._api_key = cmdop_api_key
        self._machine = machine
        self._client: AsyncCMDOPClient | None = None

    @property
    def name(self) -> str:
        return "agent"

    @property
    def description(self) -> str:
        return "Run AI agent task on remote machine"

    async def _get_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client."""
        if self._client is None:
            from cmdop import AsyncCMDOPClient

            self._client = AsyncCMDOPClient.remote(api_key=self._api_key)

            if self._machine:
                await self._client.terminal.set_machine(self._machine)

        return self._client

    async def handle(self, command: Command, send: SendCallback) -> None:
        """Run AI agent task via CMDOP."""
        if not command.args_text:
            await send("Usage: /agent <task description>")
            return

        try:
            client = await self._get_client()

            # Run agent with the task
            result = await client.agent.run(command.args_text)

            # Format response
            if result.success:
                response = result.text or "Task completed successfully."
            else:
                response = f"Agent error: {result.error or 'Unknown error'}"

            await send(response)

        except Exception as e:
            logger.exception("Agent task failed")
            await send(f"Error: {e}")

    async def close(self) -> None:
        """Close CMDOP client."""
        if self._client is not None:
            await self._client.close()
            self._client = None
