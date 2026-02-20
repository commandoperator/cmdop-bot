"""Telegram bot implementation using aiogram."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from cmdop_bot.core.base import BaseChannel
from cmdop_bot.core.cmdop_handler import CMDOPHandler
from cmdop_bot.core.permissions import PermissionManager
from cmdop_bot.models import User, Message
from cmdop_bot.channels.telegram.formatter import TelegramFormatter
from cmdop_bot.channels.telegram.handlers import (
    StartHandler,
    HelpHandler,
    ShellHandler,
    AgentHandler,
    FilesHandler,
    MachineHandler,
)

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage

logger = logging.getLogger(__name__)


class TelegramBot(BaseChannel):
    """Telegram bot using aiogram with CMDOP SDK integration.

    Example:
        >>> from cmdop_bot import Model
        >>> from cmdop_bot.channels.telegram import TelegramBot
        >>>
        >>> bot = TelegramBot(
        ...     token="123:ABC",
        ...     cmdop_api_key="cmd_xxx",
        ...     allowed_users=[123456789],
        ...     model=Model.balanced(),
        ... )
        >>> bot.run()
    """

    def __init__(
        self,
        token: str,
        cmdop_api_key: str,
        *,
        allowed_users: list[int] | None = None,
        permissions: PermissionManager | None = None,
        machine: str | None = None,
        model: str | None = None,
        server: str | None = None,
        insecure: bool = False,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Telegram bot.

        Args:
            token: Telegram bot token from @BotFather
            cmdop_api_key: CMDOP API key (cmd_xxx format)
            allowed_users: List of allowed Telegram user IDs. None = allow all.
            permissions: Permission manager for fine-grained control
            machine: Target machine hostname. None = use default machine.
            model: LLM model alias for agent. Use Model class:
                - Model.cheap() - cheapest
                - Model.balanced() - recommended default
                - Model.smart() - highest quality
                - Model.fast() - fastest response
            server: gRPC server address (e.g. "grpc.cmdop.com:443" or "127.0.0.1:50051")
            insecure: Use insecure connection (for local dev)
            timeout: Default command timeout in seconds.
        """
        super().__init__(token, cmdop_api_key)
        self._allowed_users = set(allowed_users) if allowed_users else None
        self._permissions = permissions or PermissionManager()
        self._formatter = TelegramFormatter()
        self._timeout = timeout

        # CMDOP handler with all logic
        self._cmdop = CMDOPHandler(
            api_key=cmdop_api_key,
            machine=machine,
            model=model,
            server=server,
            insecure=insecure,
        )

        self._bot = None
        self._dp = None
        self._polling_task: asyncio.Task | None = None

        # Initialize handlers (lazy - will be fully setup in start())
        self._handlers_initialized = False

    def _init_handlers(self) -> None:
        """Initialize command handlers."""
        handler_kwargs = {
            "bot": self._bot,
            "cmdop": self._cmdop,
            "formatter": self._formatter,
            "allowed_users": self._allowed_users,
            "timeout": self._timeout,
        }

        self._start_handler = StartHandler(**handler_kwargs)
        self._help_handler = HelpHandler(**handler_kwargs)
        self._shell_handler = ShellHandler(**handler_kwargs)
        self._agent_handler = AgentHandler(**handler_kwargs)
        self._files_handler = FilesHandler(**handler_kwargs)
        self._machine_handler = MachineHandler(**handler_kwargs)

        self._handlers_initialized = True

    @property
    def name(self) -> str:
        return "telegram"

    async def start(self) -> None:
        """Start the bot."""
        try:
            from aiogram import Bot, Dispatcher
            from aiogram.filters import Command as CommandFilter
        except ImportError as e:
            raise ImportError(
                "aiogram is required for Telegram. Install with: pip install cmdop-bot[telegram]"
            ) from e

        self._bot = Bot(token=self._token)
        self._dp = Dispatcher()
        self._running = True

        # Initialize handlers now that bot is available
        self._init_handlers()

        # Register handlers
        self._dp.message.register(self._start_handler.handle, CommandFilter("start"))
        self._dp.message.register(self._help_handler.handle, CommandFilter("help"))
        self._dp.message.register(self._shell_handler.handle, CommandFilter("shell"))
        self._dp.message.register(self._shell_handler.handle, CommandFilter("exec"))
        self._dp.message.register(self._agent_handler.handle, CommandFilter("agent"))
        self._dp.message.register(self._machine_handler.handle, CommandFilter("machine"))
        self._dp.message.register(self._files_handler.handle_files, CommandFilter("files"))
        self._dp.message.register(self._files_handler.handle_ls, CommandFilter("ls"))
        self._dp.message.register(self._files_handler.handle_cat, CommandFilter("cat"))
        self._dp.message.register(self._handle_message)

        logger.info("Starting Telegram bot...")
        # Start polling in background task
        self._polling_task = asyncio.create_task(
            self._dp.start_polling(self._bot, handle_signals=False)
        )

    async def stop(self) -> None:
        """Stop the bot."""
        self._running = False
        logger.info("Stopping Telegram bot...")

        # Stop polling first
        if self._dp:
            try:
                await self._dp.stop_polling()
            except Exception:
                pass

        # Cancel polling task with timeout
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await asyncio.wait_for(
                    asyncio.shield(self._polling_task),
                    timeout=2.0
                )
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Close bot session
        if self._bot:
            try:
                await self._bot.session.close()
            except Exception:
                pass

        # Close CMDOP handler with timeout
        try:
            await asyncio.wait_for(self._cmdop.close(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        logger.info("Telegram bot stopped")

    async def send(self, chat_id: str, text: str) -> None:
        """Send message to chat."""
        if self._bot:
            await self._bot.send_message(
                chat_id=int(chat_id),
                text=text,
                parse_mode="MarkdownV2",
            )

    async def send_typing(self, chat_id: str) -> None:
        """Show typing indicator."""
        if self._bot:
            await self._bot.send_chat_action(chat_id=int(chat_id), action="typing")

    def _is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        if self._allowed_users is None:
            return True
        return user_id in self._allowed_users

    def _parse_message(self, msg: AiogramMessage) -> Message:
        """Convert aiogram message to our Message model."""
        user = User(
            id=str(msg.from_user.id),
            channel="telegram",
            username=msg.from_user.username,
            display_name=msg.from_user.full_name,
        )
        return Message(
            id=str(msg.message_id),
            channel="telegram",
            chat_id=str(msg.chat.id),
            user=user,
            text=msg.text or "",
            raw=msg,
        )

    async def _handle_message(self, msg: AiogramMessage) -> None:
        """Handle regular messages (non-commands) - route to agent by default."""
        if not self._is_allowed(msg.from_user.id):
            return

        text = msg.text or ""

        # Skip if empty
        if not text.strip():
            return

        # Route to agent handler (chat mode)
        await self._handle_chat_message(msg, text)

    async def _handle_chat_message(self, msg: AiogramMessage, text: str) -> None:
        """Handle chat message - send to AI agent."""
        # Send "thinking" message
        status_msg = await msg.answer("🤔 Thinking...")

        try:
            result = await self._cmdop.run_agent(text)

            # Delete status message
            try:
                await status_msg.delete()
            except Exception:
                pass

            # Format response
            if result.success:
                response_text = result.text or "Done."
                if len(response_text) > 3500:
                    response_text = response_text[:3500] + "\n... (truncated)"
                formatted = self._formatter.escape(response_text)
            else:
                formatted = self._formatter.error(result.error or "Unknown error")

            await msg.answer(formatted, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Chat message failed")
            try:
                await status_msg.delete()
            except Exception:
                pass
            error_text = self._formatter.error(str(e))
            await msg.answer(error_text, parse_mode="MarkdownV2")
