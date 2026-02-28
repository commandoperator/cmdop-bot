"""Agent command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.channels.telegram.handlers.base import BaseHandler
from cmdop_bot.models import Command
from cmdop_bot.utils.errors import friendly_error

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage

logger = logging.getLogger(__name__)


class AgentHandler(BaseHandler):
    """Handler for /agent command."""

    async def handle(self, msg: AiogramMessage) -> None:
        """Handle /agent command - run AI agent task."""
        if not self.is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        command = Command.parse_text(msg.text or "")

        if not command or not command.args_text:
            await msg.answer("Usage: `/agent <task description>`", parse_mode="MarkdownV2")
            return

        try:
            async with self.typing(msg.chat.id):
                result = await self.cmdop.run_agent(command.args_text)

            logger.info(f"Agent result: success={result.success}, text_len={len(result.text or '')}, error={result.error}")
            logger.debug(f"Agent result text: {result.text[:500] if result.text else '(empty)'}")

            if result.success:
                response_text = result.text or "Task completed successfully."
                if len(response_text) > 3500:
                    response_text = response_text[:3500] + "\n... (truncated)"
                formatted = self.formatter.escape(response_text)
            else:
                error_text = friendly_error(result.error or "Unknown error")
                formatted = self.formatter.error(error_text)

            await msg.answer(formatted, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Agent task failed")
            await self.send_error(msg, e)
