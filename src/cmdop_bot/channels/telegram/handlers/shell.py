"""Shell command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.channels.telegram.handlers.base import BaseHandler
from cmdop_bot.models import Command

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage

logger = logging.getLogger(__name__)


class ShellHandler(BaseHandler):
    """Handler for /shell and /exec commands."""

    async def handle(self, msg: AiogramMessage) -> None:
        """Handle /shell or /exec command."""
        if not self.is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        command = Command.parse_text(msg.text or "")

        if not command or not command.args_text:
            await msg.answer("Usage: `/shell <command>`", parse_mode="MarkdownV2")
            return

        await self.send_typing(msg.chat.id)

        try:
            output, exit_code = await self.cmdop.execute_shell(
                command.args_text,
                timeout=self.timeout,
            )

            # Decode output
            output_text = output.decode("utf-8", errors="replace")

            # Truncate if too long (Telegram limit is ~4096 chars)
            if len(output_text) > 3500:
                output_text = output_text[:3500] + "\n... (truncated)"

            # Format response
            if exit_code == 0:
                formatted = self.formatter.code_block(output_text)
            elif exit_code == -1:
                formatted = self.formatter.error(f"Timeout or error:\n{output_text}")
            else:
                formatted = self.formatter.code_block(f"Exit code {exit_code}:\n{output_text}")

            await msg.answer(formatted, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Shell command failed")
            await self.send_error(msg, str(e))
