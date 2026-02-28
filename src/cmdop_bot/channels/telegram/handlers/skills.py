"""Skills command handler for Telegram."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.channels.telegram.handlers.base import BaseHandler
from cmdop_bot.models import Command
from cmdop_bot.utils.errors import friendly_error

if TYPE_CHECKING:
    from aiogram.types import Message as AiogramMessage

logger = logging.getLogger(__name__)


class SkillsHandler(BaseHandler):
    """Handler for /skills and /skill commands."""

    async def handle(self, msg: AiogramMessage) -> None:
        """Handle /skills or /skill command."""
        if not self.is_allowed(msg.from_user.id):
            await msg.answer("You are not authorized to use this bot.")
            return

        command = Command.parse_text(msg.text or "")

        if not command:
            return

        # /skill <name> <prompt> — shorthand for run
        if command.name == "skill":
            if len(command.args) < 2:
                await msg.answer(
                    "Usage: `/skill <name> <prompt>`",
                    parse_mode="MarkdownV2",
                )
                return
            await self._run_skill(
                msg, command.args[0], " ".join(command.args[1:])
            )
            return

        # /skills <subcommand>
        args = command.args

        if not args:
            await msg.answer(self._usage(), parse_mode="MarkdownV2")
            return

        sub = args[0].lower()

        if sub == "list":
            await self._list_skills(msg)
        elif sub == "show" and len(args) >= 2:
            await self._show_skill(msg, args[1])
        elif sub == "run" and len(args) >= 3:
            await self._run_skill(msg, args[1], " ".join(args[2:]))
        else:
            await msg.answer(self._usage(), parse_mode="MarkdownV2")

    async def _list_skills(self, msg: AiogramMessage) -> None:
        """List available skills."""
        try:
            async with self.typing(msg.chat.id):
                skills = await self.cmdop.list_skills()

            if not skills:
                formatted = self.formatter.escape("No skills found on this machine.")
                await msg.answer(formatted, parse_mode="MarkdownV2")
                return

            lines = ["*Available Skills*\n"]
            for s in skills:
                name = self.formatter.escape(s.name)
                desc = self.formatter.escape(s.description) if s.description else ""
                origin = f" \\[{self.formatter.escape(s.origin)}\\]" if s.origin else ""
                if desc:
                    lines.append(f"`{name}`{origin}\n  {desc}")
                else:
                    lines.append(f"`{name}`{origin}")

            text = "\n".join(lines)
            if len(text) > 3500:
                text = text[:3500] + "\n\\.\\.\\. \\(truncated\\)"

            await msg.answer(text, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Skills list failed")
            await self.send_error(msg, e)

    async def _show_skill(self, msg: AiogramMessage, name: str) -> None:
        """Show skill details."""
        try:
            async with self.typing(msg.chat.id):
                detail = await self.cmdop.show_skill(name)

            if not detail.found:
                error = self.formatter.escape(detail.error or f"Skill not found: {name}")
                await msg.answer(error, parse_mode="MarkdownV2")
                return

            info = detail.info
            parts = [f"*Skill:* `{self.formatter.escape(info.name)}`"]

            if info.description:
                parts.append(f"*Description:* {self.formatter.escape(info.description)}")
            if info.author:
                parts.append(f"*Author:* {self.formatter.escape(info.author)}")
            if info.version:
                parts.append(f"*Version:* {self.formatter.escape(info.version)}")
            if info.origin:
                parts.append(f"*Origin:* {self.formatter.escape(info.origin)}")
            if detail.source:
                parts.append(f"*Source:* `{self.formatter.escape(detail.source)}`")

            if detail.content:
                preview = detail.content[:500]
                if len(detail.content) > 500:
                    preview += "\n... (truncated)"
                escaped = self.formatter.escape(preview)
                parts.append(f"\n*System prompt:*\n```\n{escaped}\n```")

            text = "\n".join(parts)
            await msg.answer(text, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Skills show failed")
            await self.send_error(msg, e)

    async def _run_skill(
        self, msg: AiogramMessage, name: str, prompt: str
    ) -> None:
        """Run a skill."""
        try:
            async with self.typing(msg.chat.id):
                result = await self.cmdop.run_skill(name, prompt)

            logger.info(
                f"Skill result: success={result.success}, "
                f"text_len={len(result.text or '')}, "
                f"duration={result.duration_ms}ms"
            )

            if result.success:
                response_text = result.text or "Skill completed successfully."
                if len(response_text) > 3500:
                    response_text = response_text[:3500] + "\n... (truncated)"

                # Add duration footer
                if result.duration_ms:
                    response_text += f"\n\n({result.duration_seconds:.1f}s)"

                formatted = self.formatter.escape(response_text)
            else:
                error_text = friendly_error(result.error or "Unknown error")
                formatted = self.formatter.error(error_text)

            await msg.answer(formatted, parse_mode="MarkdownV2")

        except Exception as e:
            logger.exception("Skill run failed")
            await self.send_error(msg, e)

    @staticmethod
    def _usage() -> str:
        """Return usage text (MarkdownV2)."""
        return (
            "*Skills Commands*\n\n"
            "`/skills list` \\- List available skills\n"
            "`/skills show <name>` \\- Show skill details\n"
            "`/skills run <name> <prompt>` \\- Run a skill\n"
            "`/skill <name> <prompt>` \\- Shorthand for run"
        )
