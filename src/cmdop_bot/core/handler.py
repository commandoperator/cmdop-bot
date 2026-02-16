"""Message handler base class."""

from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from cmdop_bot.models import Command


# Type alias for send callback
SendCallback = Callable[[str], Awaitable[None]]  # (text) -> None


class MessageHandler(ABC):
    """Base class for command handlers.

    Example:
        >>> class ShellHandler(MessageHandler):
        ...     name = "shell"
        ...     description = "Execute shell command"
        ...
        ...     async def handle(self, cmd, send):
        ...         output = await self.execute(cmd.args_text)
        ...         await send(f"```\\n{output}\\n```")
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (e.g., 'shell', 'files')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Command description for help."""
        ...

    @abstractmethod
    async def handle(self, command: Command, send: SendCallback) -> None:
        """Handle the command.

        Args:
            command: Parsed command
            send: Callback to send response
        """
        ...
