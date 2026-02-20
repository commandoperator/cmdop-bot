"""File operations command handlers."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from cmdop_bot.channels.telegram.handlers.base import BaseHandler
from cmdop_bot.models import Command

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage

logger = logging.getLogger(__name__)


class FilesHandler(BaseHandler):
    """Handler for /files, /ls, and /cat commands."""

    async def handle_files(self, msg: AiogramMessage) -> None:
        """Handle /files command - file operations."""
        if not self.is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        command = Command.parse_text(msg.text or "")

        if not command or not command.args:
            await msg.answer(
                "*File Commands*\n\n"
                "`/files ls [path]` \\- List directory\n"
                "`/files cat <path>` \\- Read file\n"
                "`/files info <path>` \\- File info",
                parse_mode="MarkdownV2",
            )
            return

        await self.send_typing(msg.chat.id)

        try:
            subcommand = command.args[0].lower()
            path = command.args[1] if len(command.args) > 1 else "."

            if subcommand in ("ls", "list"):
                await self._list_files(msg, path)
            elif subcommand in ("cat", "read"):
                await self._read_file(msg, path)
            elif subcommand == "info":
                await self._file_info(msg, path)
            else:
                escaped = self.formatter.escape(subcommand)
                await msg.answer(f"Unknown subcommand: `{escaped}`", parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("File operation failed")
            await self.send_error(msg, str(e))

    async def handle_ls(self, msg: AiogramMessage) -> None:
        """Handle /ls command - list directory."""
        if not self.is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        command = Command.parse_text(msg.text or "")
        path = command.args_text.strip() if command and command.args_text else "."

        await self.send_typing(msg.chat.id)

        try:
            await self._list_files(msg, path)
        except Exception as e:
            logger.exception("List directory failed")
            await self.send_error(msg, str(e))

    async def handle_cat(self, msg: AiogramMessage) -> None:
        """Handle /cat command - read file."""
        if not self.is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        command = Command.parse_text(msg.text or "")

        if not command or not command.args_text:
            await msg.answer("Usage: `/cat <path>`", parse_mode="MarkdownV2")
            return

        path = command.args_text.strip()
        await self.send_typing(msg.chat.id)

        try:
            await self._read_file(msg, path)
        except Exception as e:
            logger.exception("Read file failed")
            await self.send_error(msg, str(e))

    async def _list_files(self, msg: AiogramMessage, path: str) -> None:
        """List directory contents."""
        response = await self.cmdop.list_files(path)
        entries = response.entries

        if not entries:
            escaped = self.formatter.escape(path)
            await msg.answer(f"Directory is empty: `{escaped}`", parse_mode="MarkdownV2")
            return

        lines = [f"📁 `{self.formatter.escape(path)}`\n"]
        for entry in entries[:50]:  # Limit to 50 entries
            name = self.formatter.escape(entry.name)
            if entry.type.value == "directory":
                lines.append(f"  📂 `{name}/`")
            else:
                size = self._format_size(entry.size)
                lines.append(f"  📄 `{name}` \\({size}\\)")

        if len(entries) > 50:
            lines.append(f"\n\\.\\.\\. and {len(entries) - 50} more")

        await msg.answer("\n".join(lines), parse_mode="MarkdownV2")

    async def _read_file(self, msg: AiogramMessage, path: str) -> None:
        """Read file contents."""
        content = await self.cmdop.read_file(path)

        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError:
                escaped = self.formatter.escape(path)
                await msg.answer(
                    f"Binary file: `{escaped}` \\({len(content)} bytes\\)",
                    parse_mode="MarkdownV2",
                )
                return

        # Truncate long files
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"

        formatted = self.formatter.code_block(content)
        await msg.answer(formatted, parse_mode="MarkdownV2")

    async def _file_info(self, msg: AiogramMessage, path: str) -> None:
        """Get file info."""
        info = await self.cmdop.file_info(path)

        # Extract name from path
        file_name = os.path.basename(info.path) or info.path

        is_dir = info.type.value == "directory"
        lines = [
            f"📄 `{self.formatter.escape(file_name)}`",
            f"*Path:* `{self.formatter.escape(info.path)}`",
            f"*Size:* {self._format_size(info.size)}",
            f"*Type:* {'Directory' if is_dir else 'File'}",
        ]

        if info.modified_at:
            lines.append(f"*Modified:* {self.formatter.escape(str(info.modified_at))}")

        if info.permissions:
            lines.append(f"*Permissions:* `{self.formatter.escape(info.permissions)}`")

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
