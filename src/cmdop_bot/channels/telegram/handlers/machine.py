"""Machine command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.channels.telegram.handlers.base import BaseHandler
from cmdop_bot.models import Command

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage

logger = logging.getLogger(__name__)


class MachineHandler(BaseHandler):
    """Handler for /machine command."""

    async def handle(self, msg: AiogramMessage) -> None:
        """Handle /machine command - set target machine."""
        if not self.is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        command = Command.parse_text(msg.text or "")

        if not command or not command.args_text:
            await msg.answer("Usage: `/machine <hostname>`", parse_mode="MarkdownV2")
            return

        hostname = command.args_text.strip()

        try:
            full_hostname = await self.cmdop.set_machine(hostname)
            escaped = self.formatter.escape(full_hostname)
            response = f"Connected to: `{escaped}`"
            await msg.answer(response, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Set machine failed")
            await self.send_error(msg, str(e))
