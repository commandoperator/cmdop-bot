"""Base channel class."""

from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from cmdop_bot.models import Message


# Type alias for send callback
SendCallback = Callable[[str, str], Awaitable[None]]  # (chat_id, text) -> None


class BaseChannel(ABC):
    """Base class for all channel implementations.

    Subclasses must implement:
        - name: Channel identifier
        - start(): Start listening
        - stop(): Stop gracefully
        - send(): Send message
    """

    def __init__(self, token: str, cmdop_api_key: str) -> None:
        """Initialize channel.

        Args:
            token: Channel API token (Telegram, Discord, etc.)
            cmdop_api_key: CMDOP API key for remote access
        """
        self._token = token
        self._cmdop_api_key = cmdop_api_key
        self._running = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel identifier (telegram, discord, slack)."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start listening for messages."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop gracefully."""
        ...

    @abstractmethod
    async def send(self, chat_id: str, text: str) -> None:
        """Send message to chat.

        Args:
            chat_id: Target chat/channel ID
            text: Message text
        """
        ...

    @abstractmethod
    async def send_typing(self, chat_id: str) -> None:
        """Show typing indicator."""
        ...

    async def on_message(self, message: Message) -> None:
        """Handle incoming message. Override in subclass."""
        pass

    def run(self) -> None:
        """Run the bot (blocking). Convenience method."""
        import asyncio
        asyncio.run(self._run_forever())

    async def _run_forever(self) -> None:
        """Run until stopped."""
        await self.start()
        try:
            while self._running:
                await asyncio.sleep(1)
        finally:
            await self.stop()
