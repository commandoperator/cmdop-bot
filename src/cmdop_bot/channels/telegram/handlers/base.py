"""Base handler for Telegram commands."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

from cmdop_bot.utils.errors import friendly_error

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message as AiogramMessage
    from cmdop_bot.core.cmdop_handler import CMDOPHandler
    from cmdop_bot.channels.telegram.formatter import TelegramFormatter

logger = logging.getLogger(__name__)

# Telegram typing indicator lasts ~5s, resend every 4s to keep it alive
_TYPING_INTERVAL = 4.0


class BaseHandler:
    """Base class for Telegram command handlers."""

    def __init__(
        self,
        bot: Bot,
        cmdop: CMDOPHandler,
        formatter: TelegramFormatter,
        allowed_users: set[int] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize handler.

        Args:
            bot: Aiogram bot instance
            cmdop: CMDOP handler for SDK operations
            formatter: Telegram formatter for messages
            allowed_users: Set of allowed user IDs. None = allow all.
            timeout: Default timeout for operations
        """
        self.bot = bot
        self.cmdop = cmdop
        self.formatter = formatter
        self.allowed_users = allowed_users
        self.timeout = timeout

    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        if self.allowed_users is None:
            return True
        return user_id in self.allowed_users

    async def send_typing(self, chat_id: int) -> None:
        """Show typing indicator (single shot, for quick operations)."""
        await self.bot.send_chat_action(chat_id=chat_id, action="typing")

    @asynccontextmanager
    async def typing(self, chat_id: int) -> AsyncIterator[None]:
        """Continuous typing indicator — keeps "typing..." visible until the block exits.

        Usage:
            async with self.typing(msg.chat.id):
                result = await long_running_operation()
        """
        async def _loop() -> None:
            try:
                while True:
                    await self.bot.send_chat_action(chat_id=chat_id, action="typing")
                    await asyncio.sleep(_TYPING_INTERVAL)
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(_loop())
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def send_error(self, msg: AiogramMessage, error: str | Exception) -> None:
        """Send user-friendly error message."""
        error_msg = self.formatter.error(friendly_error(error))
        await msg.answer(error_msg, parse_mode="MarkdownV2")
