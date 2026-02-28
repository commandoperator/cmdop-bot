"""Skills command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.core.handler import MessageHandler, SendCallback
from cmdop_bot.models import Command

if TYPE_CHECKING:
    from cmdop import AsyncCMDOPClient

logger = logging.getLogger(__name__)


class SkillsHandler(MessageHandler):
    """Handle /skills command - list, inspect, and run skills.

    Example:
        >>> handler = SkillsHandler(cmdop_api_key="cmdop_xxx")
        >>> await handler.handle(command, send)
    """

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self._api_key = cmdop_api_key
        self._machine = machine
        self._timeout = timeout
        self._client: AsyncCMDOPClient | None = None

    @property
    def name(self) -> str:
        return "skills"

    @property
    def description(self) -> str:
        return "List, inspect, and run skills"

    async def _get_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client."""
        if self._client is None:
            from cmdop import AsyncCMDOPClient

            self._client = AsyncCMDOPClient.remote(api_key=self._api_key)

            if self._machine:
                await self._client.skills.set_machine(self._machine)

        return self._client

    async def handle(self, command: Command, send: SendCallback) -> None:
        """Handle /skills command with subcommand dispatch."""
        args = command.args

        if not args:
            await send(
                "Usage:\n"
                "  /skills list — List available skills\n"
                "  /skills show <name> — Show skill details\n"
                "  /skills run <name> <prompt> — Run a skill\n"
                "  /skill <name> <prompt> — Shorthand for run"
            )
            return

        sub = args[0].lower()

        try:
            if sub == "list":
                await self._list_skills(send)
            elif sub == "show" and len(args) >= 2:
                await self._show_skill(args[1], send)
            elif sub == "run" and len(args) >= 3:
                await self._run_skill(args[1], " ".join(args[2:]), send)
            else:
                await send("Unknown subcommand. Use: list, show, run")
        except Exception as e:
            logger.exception("Skills command failed")
            await send(f"Error: {e}")

    async def _list_skills(self, send: SendCallback) -> None:
        """List available skills."""
        client = await self._get_client()
        skills = await client.skills.list()

        if not skills:
            await send("No skills found on this machine.")
            return

        lines = ["Available skills:\n"]
        for s in skills:
            desc = f" — {s.description}" if s.description else ""
            origin = f" [{s.origin}]" if s.origin else ""
            lines.append(f"  {s.name}{desc}{origin}")

        await send("\n".join(lines))

    async def _show_skill(self, name: str, send: SendCallback) -> None:
        """Show skill details."""
        client = await self._get_client()
        detail = await client.skills.show(name)

        if not detail.found:
            await send(f"Skill not found: {name}\n{detail.error}")
            return

        info = detail.info
        lines = [f"Skill: {info.name}"]
        if info.description:
            lines.append(f"Description: {info.description}")
        if info.author:
            lines.append(f"Author: {info.author}")
        if info.version:
            lines.append(f"Version: {info.version}")
        if info.origin:
            lines.append(f"Origin: {info.origin}")
        if detail.source:
            lines.append(f"Source: {detail.source}")
        if detail.content:
            preview = detail.content[:500]
            if len(detail.content) > 500:
                preview += "\n... (truncated)"
            lines.append(f"\nSystem prompt:\n```\n{preview}\n```")

        await send("\n".join(lines))

    async def _run_skill(self, name: str, prompt: str, send: SendCallback) -> None:
        """Run a skill."""
        from cmdop.models.skills import SkillRunOptions

        client = await self._get_client()
        options = SkillRunOptions(timeout_seconds=int(self._timeout))
        result = await client.skills.run(name, prompt, options=options)

        if result.success:
            text = result.text or "Skill completed successfully."
            duration = f"\n\n({result.duration_seconds:.1f}s)" if result.duration_ms else ""
            await send(f"{text}{duration}")
        else:
            await send(f"Skill error: {result.error or 'Unknown error'}")

    async def close(self) -> None:
        """Close CMDOP client."""
        if self._client is not None:
            await self._client.close()
            self._client = None
