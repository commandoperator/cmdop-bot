"""Slack app implementation using slack-bolt."""

from __future__ import annotations

import logging
from typing import Any

from cmdop_bot.core.base import BaseChannel
from cmdop_bot.core.cmdop_handler import CMDOPHandler
from cmdop_bot.core.permissions import PermissionManager
from cmdop_bot.channels.slack.blocks import BlockBuilder

logger = logging.getLogger(__name__)


class SlackApp(BaseChannel):
    """Slack app using slack-bolt with CMDOP SDK integration.

    Uses Socket Mode for real-time events without public webhooks.

    Example:
        >>> from cmdop_bot import Model
        >>> app = SlackApp(
        ...     bot_token="xoxb-YOUR-BOT-TOKEN",
        ...     app_token="xapp-YOUR-APP-TOKEN",
        ...     cmdop_api_key="cmd_xxx",
        ...     model=Model.balanced(),  # Optional: AI model tier
        ... )
        >>> app.run()
    """

    def __init__(
        self,
        bot_token: str,
        app_token: str,
        cmdop_api_key: str,
        *,
        allowed_users: list[str] | None = None,
        permissions: PermissionManager | None = None,
        machine: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Slack app.

        Args:
            bot_token: Slack bot token (xoxb-...)
            app_token: Slack app-level token for Socket Mode (xapp-...)
            cmdop_api_key: CMDOP API key (cmd_xxx format)
            allowed_users: List of allowed Slack user IDs. None = allow all.
            permissions: Permission manager for fine-grained control
            machine: Target machine hostname. None = use default machine.
            model: Model tier alias (e.g. Model.balanced()). None = server default.
            timeout: Default command timeout in seconds.
        """
        super().__init__(bot_token, cmdop_api_key)
        self._app_token = app_token
        self._allowed_users = set(allowed_users) if allowed_users else None
        self._permissions = permissions or PermissionManager()
        self._timeout = timeout

        # CMDOP handler with all logic
        self._cmdop = CMDOPHandler(api_key=cmdop_api_key, machine=machine, model=model)

        self._app: Any = None
        self._handler: Any = None

    @property
    def name(self) -> str:
        return "slack"

    def _is_allowed(self, user_id: str) -> bool:
        """Check if user is allowed to use the app."""
        if self._allowed_users is None:
            return True
        return user_id in self._allowed_users

    async def start(self) -> None:
        """Start the app."""
        try:
            from slack_bolt.async_app import AsyncApp
            from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
        except ImportError as e:
            raise ImportError(
                "slack-bolt is required for Slack. Install with: pip install cmdop-sdk[slack]"
            ) from e

        self._app = AsyncApp(token=self._token)
        self._running = True

        # Register command handler
        @self._app.command("/cmdop")
        async def handle_cmdop(ack, command, respond):
            await ack()
            await self._handle_command(command, respond)

        # Start Socket Mode handler
        self._handler = AsyncSocketModeHandler(self._app, self._app_token)
        logger.info("Starting Slack app with Socket Mode...")
        await self._handler.start_async()

    async def _handle_command(self, command: dict, respond) -> None:
        """Handle /cmdop command."""
        user_id = command.get("user_id", "")
        text = command.get("text", "").strip()

        if not self._is_allowed(user_id):
            await respond(
                blocks=BlockBuilder.error_message(
                    "Access Denied",
                    "You are not authorized to use this app.",
                )
            )
            return

        # Parse subcommand
        parts = text.split(maxsplit=1)
        subcommand = parts[0].lower() if parts else "help"
        args = parts[1] if len(parts) > 1 else ""

        if subcommand == "help":
            await respond(blocks=BlockBuilder.help_message())

        elif subcommand == "shell" or subcommand == "exec":
            if not args:
                await respond(text="Usage: `/cmdop shell <command>`")
                return
            await self._handle_shell(args, respond)

        elif subcommand == "agent":
            if not args:
                await respond(text="Usage: `/cmdop agent <task>`")
                return
            await self._handle_agent(args, respond)

        elif subcommand == "machine":
            if not args:
                await respond(text="Usage: `/cmdop machine <hostname>`")
                return
            await self._handle_machine(args, respond)

        elif subcommand == "status":
            await self._handle_status(respond)

        elif subcommand == "ls":
            path = args.strip() if args else "."
            await self._handle_ls(path, respond)

        elif subcommand == "cat":
            if not args:
                await respond(text="Usage: `/cmdop cat <path>`")
                return
            await self._handle_cat(args.strip(), respond)

        else:
            await respond(
                text=f"Unknown command: `{subcommand}`. Use `/cmdop help` for available commands."
            )

    async def _handle_shell(self, command: str, respond) -> None:
        """Handle shell command."""
        try:
            output, exit_code = await self._cmdop.execute_shell(
                command,
                timeout=self._timeout,
            )

            # Decode output
            output_text = output.decode("utf-8", errors="replace")

            blocks = BlockBuilder.command_result(
                command=command,
                output=output_text,
                exit_code=exit_code,
            )

            await respond(blocks=blocks)

        except Exception as e:
            logger.exception("Shell command failed")
            await respond(
                blocks=BlockBuilder.error_message("Command Failed", str(e))
            )

    async def _handle_agent(self, task: str, respond) -> None:
        """Handle agent command."""
        try:
            result = await self._cmdop.run_agent(task)

            blocks = BlockBuilder.agent_result(
                task=task,
                result=result.text or "Task completed.",
                success=result.success,
            )

            await respond(blocks=blocks)

        except Exception as e:
            logger.exception("Agent task failed")
            await respond(
                blocks=BlockBuilder.error_message("Agent Failed", str(e))
            )

    async def _handle_machine(self, hostname: str, respond) -> None:
        """Handle machine command."""
        try:
            full_hostname = await self._cmdop.set_machine(hostname)
            client = await self._cmdop.get_client()
            session = client.terminal.current_session

            blocks = BlockBuilder.machine_info(
                hostname=full_hostname,
                os=session.os if session else "unknown",
                shell=session.shell if session else "unknown",
            )

            await respond(blocks=blocks)

        except Exception as e:
            logger.exception("Machine selection failed")
            await respond(
                blocks=BlockBuilder.error_message("Connection Failed", str(e))
            )

    async def _handle_status(self, respond) -> None:
        """Handle status command."""
        try:
            fields = [
                ("Machine", self._cmdop.machine or "(default)"),
                ("Model", self._cmdop.model or "(default)"),
            ]

            client = await self._cmdop.get_client()
            current_session = client.terminal.current_session
            if current_session:
                fields.append(("Session", f"`{current_session.machine_hostname}`"))

            blocks = [
                BlockBuilder.header(":electric_plug: Connection Status"),
                BlockBuilder.fields(fields),
            ]

            await respond(blocks=blocks)

        except Exception as e:
            await respond(
                blocks=BlockBuilder.error_message("Status Error", str(e))
            )

    async def _handle_ls(self, path: str, respond) -> None:
        """Handle ls command."""
        try:
            response = await self._cmdop.list_files(path)
            entries = response.entries

            blocks = BlockBuilder.file_list(path, entries)
            await respond(blocks=blocks)

        except Exception as e:
            logger.exception("List directory failed")
            await respond(
                blocks=BlockBuilder.error_message("List Failed", str(e))
            )

    async def _handle_cat(self, path: str, respond) -> None:
        """Handle cat command."""
        try:
            content = await self._cmdop.read_file(path)

            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    await respond(text=f"Binary file: `{path}` ({len(content)} bytes)")
                    return

            blocks = BlockBuilder.file_content(path, content)
            await respond(blocks=blocks)

        except Exception as e:
            logger.exception("Read file failed")
            await respond(
                blocks=BlockBuilder.error_message("Read Failed", str(e))
            )

    async def stop(self) -> None:
        """Stop the app."""
        self._running = False
        if self._handler:
            await self._handler.close_async()
        await self._cmdop.close()
        logger.info("Slack app stopped")

    async def send(self, chat_id: str, text: str) -> None:
        """Send message to channel."""
        if self._app:
            await self._app.client.chat_postMessage(channel=chat_id, text=text)
