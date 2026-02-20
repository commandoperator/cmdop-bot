"""Base channel class."""

import asyncio
import signal
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
        self._shutdown_event: asyncio.Event | None = None

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
        try:
            asyncio.run(self._run_with_shutdown())
        except KeyboardInterrupt:
            pass  # Clean exit on Ctrl+C

    async def _run_with_shutdown(self) -> None:
        """Run with graceful shutdown on SIGINT/SIGTERM."""
        self._shutdown_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        # Setup signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)

        try:
            await self.start()
            # Wait for shutdown signal
            await self._shutdown_event.wait()
        finally:
            # Stop with timeout to avoid hanging
            try:
                await asyncio.wait_for(self.stop(), timeout=5.0)
            except asyncio.TimeoutError:
                pass  # Force exit if stop() hangs

    def _signal_handler(self) -> None:
        """Handle shutdown signal."""
        if self._shutdown_event and not self._shutdown_event.is_set():
            self._shutdown_event.set()
