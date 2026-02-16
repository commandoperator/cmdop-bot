"""Integration Hub - Multi-channel management."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cmdop import AsyncCMDOPClient
    from cmdop_bot.core.base import BaseChannel

logger = logging.getLogger(__name__)


class IntegrationHub:
    """Multi-channel integration hub.

    Manages multiple bot channels with a shared CMDOP client.

    Example:
        >>> hub = IntegrationHub(cmdop_api_key="cmd_xxx")
        >>> hub.add_channel(TelegramBot(token="tg_xxx", cmdop_api_key="cmd_xxx"))
        >>> hub.add_channel(DiscordBot(token="dc_xxx", cmdop_api_key="cmd_xxx"))
        >>> await hub.start()
    """

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
    ) -> None:
        """Initialize hub.

        Args:
            cmdop_api_key: CMDOP API key for shared client
            machine: Default target machine for all channels
        """
        self._api_key = cmdop_api_key
        self._machine = machine
        self._channels: list[BaseChannel] = []
        self._client: AsyncCMDOPClient | None = None
        self._running = False

    def add_channel(self, channel: BaseChannel) -> IntegrationHub:
        """Add a channel to the hub.

        Args:
            channel: Channel instance to add

        Returns:
            Self for chaining
        """
        self._channels.append(channel)
        logger.info(f"Added channel: {channel.name}")
        return self

    async def _get_client(self) -> AsyncCMDOPClient:
        """Get or create shared CMDOP client."""
        if self._client is None:
            from cmdop import AsyncCMDOPClient

            self._client = AsyncCMDOPClient.remote(api_key=self._api_key)

            if self._machine:
                await self._client.terminal.set_machine(self._machine)
                logger.info(f"Connected to machine: {self._machine}")

        return self._client

    async def start(self) -> None:
        """Start all channels concurrently."""
        if not self._channels:
            raise ValueError("No channels added to hub")

        self._running = True

        # Initialize shared client
        await self._get_client()

        # Start all channels concurrently
        logger.info(f"Starting {len(self._channels)} channels...")

        tasks = [
            asyncio.create_task(self._run_channel(channel))
            for channel in self._channels
        ]

        # Wait for all channels (they run forever until stopped)
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Hub cancelled, stopping channels...")
            await self.stop()

    async def _run_channel(self, channel: BaseChannel) -> None:
        """Run a single channel with error handling."""
        try:
            logger.info(f"Starting channel: {channel.name}")
            await channel.start()
        except Exception as e:
            logger.exception(f"Channel {channel.name} failed: {e}")
            raise

    async def stop(self) -> None:
        """Stop all channels."""
        self._running = False

        # Stop all channels concurrently
        stop_tasks = [
            asyncio.create_task(self._stop_channel(channel))
            for channel in self._channels
        ]

        await asyncio.gather(*stop_tasks, return_exceptions=True)

        # Close shared client
        if self._client:
            await self._client.close()
            self._client = None

        logger.info("Hub stopped")

    async def _stop_channel(self, channel: BaseChannel) -> None:
        """Stop a single channel with error handling."""
        try:
            logger.info(f"Stopping channel: {channel.name}")
            await channel.stop()
        except Exception as e:
            logger.exception(f"Error stopping channel {channel.name}: {e}")

    async def __aenter__(self) -> IntegrationHub:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.stop()

    @property
    def channels(self) -> list[BaseChannel]:
        """Get list of registered channels."""
        return self._channels.copy()

    @property
    def is_running(self) -> bool:
        """Check if hub is running."""
        return self._running


# Convenience functions for quick setup

def telegram_bot(
    token: str,
    cmdop_api_key: str,
    *,
    allowed_users: list[int] | None = None,
    machine: str | None = None,
):
    """Create a ready-to-run Telegram bot.

    Example:
        >>> bot = telegram_bot("tg_token", "cmd_xxx", allowed_users=[123])
        >>> bot.run()
    """
    from cmdop_bot.channels.telegram import TelegramBot

    return TelegramBot(
        token=token,
        cmdop_api_key=cmdop_api_key,
        allowed_users=allowed_users,
        machine=machine,
    )


def discord_bot(
    token: str,
    cmdop_api_key: str,
    *,
    guild_ids: list[int] | None = None,
    allowed_users: list[int] | None = None,
    machine: str | None = None,
):
    """Create a ready-to-run Discord bot.

    Example:
        >>> bot = discord_bot("dc_token", "cmd_xxx", guild_ids=[123])
        >>> bot.run()
    """
    from cmdop_bot.channels.discord import DiscordBot

    return DiscordBot(
        token=token,
        cmdop_api_key=cmdop_api_key,
        guild_ids=guild_ids,
        allowed_users=allowed_users,
        machine=machine,
    )


def slack_app(
    bot_token: str,
    app_token: str,
    cmdop_api_key: str,
    *,
    allowed_users: list[str] | None = None,
    machine: str | None = None,
):
    """Create a ready-to-run Slack app.

    Example:
        >>> app = slack_app("xoxb-xxx", "xapp-xxx", "cmd_xxx")
        >>> app.run()
    """
    from cmdop_bot.channels.slack import SlackApp

    return SlackApp(
        bot_token=bot_token,
        app_token=app_token,
        cmdop_api_key=cmdop_api_key,
        allowed_users=allowed_users,
        machine=machine,
    )
