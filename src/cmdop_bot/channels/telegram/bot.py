"""Telegram bot implementation using aiogram."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.core.base import BaseChannel
from cmdop_bot.core.permissions import PermissionManager
from cmdop_bot.models import User, Message, Command
from cmdop_bot.channels.telegram.formatter import TelegramFormatter

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage
    from cmdop import AsyncCMDOPClient

logger = logging.getLogger(__name__)


class TelegramBot(BaseChannel):
    """Telegram bot using aiogram with CMDOP SDK integration.

    Example:
        >>> bot = TelegramBot(
        ...     token="123:ABC",
        ...     cmdop_api_key="cmd_xxx",
        ...     allowed_users=[123456789],
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
        timeout: float = 30.0,
    ) -> None:
        """Initialize Telegram bot.

        Args:
            token: Telegram bot token from @BotFather
            cmdop_api_key: CMDOP API key (cmd_xxx format)
            allowed_users: List of allowed Telegram user IDs. None = allow all.
            permissions: Permission manager for fine-grained control
            machine: Target machine hostname. None = use default machine.
            timeout: Default command timeout in seconds.
        """
        super().__init__(token, cmdop_api_key)
        self._allowed_users = set(allowed_users) if allowed_users else None
        self._permissions = permissions or PermissionManager()
        self._formatter = TelegramFormatter()
        self._machine = machine
        self._timeout = timeout

        self._bot = None
        self._dp = None
        self._cmdop_client: AsyncCMDOPClient | None = None

    @property
    def name(self) -> str:
        return "telegram"

    async def _get_cmdop_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client (lazy initialization)."""
        if self._cmdop_client is None:
            from cmdop import AsyncCMDOPClient

            self._cmdop_client = AsyncCMDOPClient.remote(api_key=self._cmdop_api_key)

            if self._machine:
                await self._cmdop_client.terminal.set_machine(self._machine)
                logger.info(f"Connected to machine: {self._machine}")

        return self._cmdop_client

    async def start(self) -> None:
        """Start the bot."""
        try:
            from aiogram import Bot, Dispatcher
            from aiogram.filters import Command as CommandFilter
        except ImportError as e:
            raise ImportError(
                "aiogram is required for Telegram. Install with: pip install cmdop-sdk[telegram]"
            ) from e

        self._bot = Bot(token=self._token)
        self._dp = Dispatcher()
        self._running = True

        # Register handlers
        self._dp.message.register(self._handle_start, CommandFilter("start"))
        self._dp.message.register(self._handle_help, CommandFilter("help"))
        self._dp.message.register(self._handle_shell, CommandFilter("shell"))
        self._dp.message.register(self._handle_exec, CommandFilter("exec"))
        self._dp.message.register(self._handle_agent, CommandFilter("agent"))
        self._dp.message.register(self._handle_machine, CommandFilter("machine"))
        self._dp.message.register(self._handle_files, CommandFilter("files"))
        self._dp.message.register(self._handle_ls, CommandFilter("ls"))
        self._dp.message.register(self._handle_cat, CommandFilter("cat"))
        self._dp.message.register(self._handle_message)

        logger.info("Starting Telegram bot...")
        await self._dp.start_polling(self._bot)

    async def stop(self) -> None:
        """Stop the bot."""
        self._running = False
        if self._dp:
            await self._dp.stop_polling()
        if self._bot:
            await self._bot.session.close()
        if self._cmdop_client:
            await self._cmdop_client.close()
            self._cmdop_client = None
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

    async def _handle_start(self, msg: AiogramMessage) -> None:
        """Handle /start command."""
        if not self._is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        welcome = (
            "*Welcome to CMDOP Bot\\!*\n\n"
            "Available commands:\n"
            "• `/shell <command>` \\- Execute shell command\n"
            "• `/exec <command>` \\- Same as /shell\n"
            "• `/agent <task>` \\- Run AI agent task\n"
            "• `/machine <hostname>` \\- Set target machine\n"
            "• `/files ls|cat <path>` \\- File operations\n"
            "• `/ls [path]` \\- List directory\n"
            "• `/cat <path>` \\- Read file\n"
            "• `/help` \\- Show this help\n"
        )
        await msg.answer(welcome, parse_mode="MarkdownV2")

    async def _handle_help(self, msg: AiogramMessage) -> None:
        """Handle /help command."""
        help_text = (
            "*CMDOP Bot Commands*\n\n"
            "*Shell:*\n"
            "`/shell <command>` \\- Execute shell command\n"
            "`/exec <command>` \\- Same as /shell\n\n"
            "*Files:*\n"
            "`/files ls [path]` \\- List directory\n"
            "`/files cat <path>` \\- Read file\n"
            "`/ls [path]` \\- List directory \\(shortcut\\)\n"
            "`/cat <path>` \\- Read file \\(shortcut\\)\n\n"
            "*AI Agent:*\n"
            "`/agent <task>` \\- Run AI agent task\n\n"
            "*Settings:*\n"
            "`/machine <hostname>` \\- Set target machine\n"
            "`/help` \\- Show this help\n"
        )
        await msg.answer(help_text, parse_mode="MarkdownV2")

    async def _handle_machine(self, msg: AiogramMessage) -> None:
        """Handle /machine command - set target machine."""
        if not self._is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        message = self._parse_message(msg)
        command = Command.parse(message.text, message)

        if not command or not command.args_text:
            await msg.answer("Usage: `/machine <hostname>`", parse_mode="MarkdownV2")
            return

        hostname = command.args_text.strip()

        try:
            client = await self._get_cmdop_client()
            session = await client.terminal.set_machine(hostname)

            response = (
                f"Connected to: `{self._formatter.escape(session.machine_hostname)}`\n"
                f"OS: {self._formatter.escape(session.os or 'unknown')}\n"
                f"Shell: {self._formatter.escape(session.shell or 'unknown')}"
            )
            await msg.answer(response, parse_mode="MarkdownV2")

        except Exception as e:
            error_msg = self._formatter.error(str(e))
            await msg.answer(error_msg, parse_mode="MarkdownV2")

    async def _handle_shell(self, msg: AiogramMessage) -> None:
        """Handle /shell command."""
        await self._execute_command(msg)

    async def _handle_exec(self, msg: AiogramMessage) -> None:
        """Handle /exec command (alias for /shell)."""
        await self._execute_command(msg)

    async def _execute_command(self, msg: AiogramMessage) -> None:
        """Execute shell command via CMDOP."""
        if not self._is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        message = self._parse_message(msg)
        command = Command.parse(message.text, message)

        if not command or not command.args_text:
            await msg.answer("Usage: `/shell <command>`", parse_mode="MarkdownV2")
            return

        await self.send_typing(str(msg.chat.id))

        try:
            client = await self._get_cmdop_client()

            output, exit_code = await client.terminal.execute(
                command.args_text,
                timeout=self._timeout,
            )

            # Decode output
            output_text = output.decode("utf-8", errors="replace")

            # Truncate if too long (Telegram limit is ~4096 chars)
            if len(output_text) > 3500:
                output_text = output_text[:3500] + "\n... (truncated)"

            # Format response
            if exit_code == 0:
                formatted = self._formatter.code_block(output_text)
            elif exit_code == -1:
                formatted = self._formatter.error(f"Timeout or error:\n{output_text}")
            else:
                formatted = self._formatter.code_block(f"Exit code {exit_code}:\n{output_text}")

            await msg.answer(formatted, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Shell command failed")
            error_msg = self._formatter.error(str(e))
            await msg.answer(error_msg, parse_mode="MarkdownV2")

    async def _handle_agent(self, msg: AiogramMessage) -> None:
        """Handle /agent command - run AI agent task."""
        if not self._is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        message = self._parse_message(msg)
        command = Command.parse(message.text, message)

        if not command or not command.args_text:
            await msg.answer("Usage: `/agent <task description>`", parse_mode="MarkdownV2")
            return

        await self.send_typing(str(msg.chat.id))

        try:
            client = await self._get_cmdop_client()

            # Run agent with the task
            result = await client.agent.run(command.args_text)

            # Format response
            if result.success:
                response_text = result.text or "Task completed successfully."
                # Truncate if too long
                if len(response_text) > 3500:
                    response_text = response_text[:3500] + "\n... (truncated)"
                formatted = self._formatter.escape(response_text)
            else:
                error_text = result.error or "Unknown error"
                formatted = self._formatter.error(error_text)

            await msg.answer(formatted, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Agent task failed")
            error_msg = self._formatter.error(str(e))
            await msg.answer(error_msg, parse_mode="MarkdownV2")

    async def _handle_files(self, msg: AiogramMessage) -> None:
        """Handle /files command - file operations."""
        if not self._is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        message = self._parse_message(msg)
        command = Command.parse(message.text, message)

        if not command or not command.args:
            await msg.answer(
                "*File Commands*\n\n"
                "`/files ls [path]` \\- List directory\n"
                "`/files cat <path>` \\- Read file\n"
                "`/files info <path>` \\- File info",
                parse_mode="MarkdownV2",
            )
            return

        await self.send_typing(str(msg.chat.id))

        try:
            client = await self._get_cmdop_client()

            subcommand = command.args[0].lower()
            path = command.args[1] if len(command.args) > 1 else "."

            if subcommand in ("ls", "list"):
                await self._files_list(msg, client, path)
            elif subcommand in ("cat", "read"):
                await self._files_cat(msg, client, path)
            elif subcommand == "info":
                await self._files_info(msg, client, path)
            else:
                await msg.answer(f"Unknown subcommand: `{self._formatter.escape(subcommand)}`", parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("File operation failed")
            error_msg = self._formatter.error(str(e))
            await msg.answer(error_msg, parse_mode="MarkdownV2")

    async def _handle_ls(self, msg: AiogramMessage) -> None:
        """Handle /ls command - list directory."""
        if not self._is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        message = self._parse_message(msg)
        command = Command.parse(message.text, message)
        path = command.args_text.strip() if command and command.args_text else "."

        await self.send_typing(str(msg.chat.id))

        try:
            client = await self._get_cmdop_client()
            await self._files_list(msg, client, path)
        except Exception as e:
            logger.exception("List directory failed")
            error_msg = self._formatter.error(str(e))
            await msg.answer(error_msg, parse_mode="MarkdownV2")

    async def _handle_cat(self, msg: AiogramMessage) -> None:
        """Handle /cat command - read file."""
        if not self._is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        message = self._parse_message(msg)
        command = Command.parse(message.text, message)

        if not command or not command.args_text:
            await msg.answer("Usage: `/cat <path>`", parse_mode="MarkdownV2")
            return

        path = command.args_text.strip()
        await self.send_typing(str(msg.chat.id))

        try:
            client = await self._get_cmdop_client()
            await self._files_cat(msg, client, path)
        except Exception as e:
            logger.exception("Read file failed")
            error_msg = self._formatter.error(str(e))
            await msg.answer(error_msg, parse_mode="MarkdownV2")

    async def _files_list(
        self,
        msg: AiogramMessage,
        client: AsyncCMDOPClient,
        path: str,
    ) -> None:
        """List directory contents."""
        response = await client.files.list(path)
        entries = response.entries

        if not entries:
            await msg.answer(f"Directory is empty: `{self._formatter.escape(path)}`", parse_mode="MarkdownV2")
            return

        lines = [f"📁 `{self._formatter.escape(path)}`\n"]
        for entry in entries[:50]:  # Limit to 50 entries
            name = self._formatter.escape(entry.name)
            if entry.type.value == "directory":
                lines.append(f"  📂 `{name}/`")
            else:
                size = self._format_size(entry.size)
                lines.append(f"  📄 `{name}` \\({size}\\)")

        if len(entries) > 50:
            lines.append(f"\n\\.\\.\\. and {len(entries) - 50} more")

        await msg.answer("\n".join(lines), parse_mode="MarkdownV2")

    async def _files_cat(
        self,
        msg: AiogramMessage,
        client: AsyncCMDOPClient,
        path: str,
    ) -> None:
        """Read file contents."""
        content = await client.files.read(path)

        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError:
                await msg.answer(f"Binary file: `{self._formatter.escape(path)}` \\({len(content)} bytes\\)", parse_mode="MarkdownV2")
                return

        # Truncate long files
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"

        formatted = self._formatter.code_block(content)
        await msg.answer(formatted, parse_mode="MarkdownV2")

    async def _files_info(
        self,
        msg: AiogramMessage,
        client: AsyncCMDOPClient,
        path: str,
    ) -> None:
        """Get file info."""
        info = await client.files.info(path)

        # Extract name from path
        import os
        file_name = os.path.basename(info.path) or info.path

        is_dir = info.type.value == "directory"
        lines = [
            f"📄 `{self._formatter.escape(file_name)}`",
            f"*Path:* `{self._formatter.escape(info.path)}`",
            f"*Size:* {self._format_size(info.size)}",
            f"*Type:* {'Directory' if is_dir else 'File'}",
        ]

        if info.modified_at:
            lines.append(f"*Modified:* {self._formatter.escape(str(info.modified_at))}")

        if info.permissions:
            lines.append(f"*Permissions:* `{self._formatter.escape(info.permissions)}`")

        await msg.answer("\n".join(lines), parse_mode="MarkdownV2")

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size for display."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

    async def _handle_message(self, msg: AiogramMessage) -> None:
        """Handle regular messages (non-commands)."""
        if not self._is_allowed(msg.from_user.id):
            return

        message = self._parse_message(msg)
        await self.on_message(message)
