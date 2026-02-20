"""Start and help command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cmdop_bot.channels.telegram.handlers.base import BaseHandler

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage


class StartHandler(BaseHandler):
    """Handler for /start command."""

    async def handle(self, msg: AiogramMessage) -> None:
        """Handle /start command."""
        if not self.is_allowed(msg.from_user.id):
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


class HelpHandler(BaseHandler):
    """Handler for /help command."""

    async def handle(self, msg: AiogramMessage) -> None:
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
