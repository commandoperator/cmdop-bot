"""Agent command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.channels.telegram.handlers.base import BaseHandler
from cmdop_bot.models import Command

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

        # Send "thinking" message
        status_msg = await msg.answer("🤔 Thinking...")

        try:
            # Use regular run() - wait for full result
            result = await self.cmdop.run_agent(command.args_text)

            # Debug log
            logger.info(f"Agent result: success={result.success}, text_len={len(result.text or '')}, error={result.error}")
            logger.debug(f"Agent result text: {result.text[:500] if result.text else '(empty)'}")

            # Delete status message
            try:
                await status_msg.delete()
            except Exception:
                pass

            # Format final response
            if result.success:
                response_text = result.text or "Task completed successfully."
                # Truncate if too long
                if len(response_text) > 3500:
                    response_text = response_text[:3500] + "\n... (truncated)"
                formatted = self.formatter.escape(response_text)
            else:
                error_text = result.error or "Unknown error"
                formatted = self.formatter.error(error_text)

            await msg.answer(formatted, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Agent task failed")
            # Try to delete status message
            try:
                await status_msg.delete()
            except Exception:
                pass
            await self.send_error(msg, str(e))
