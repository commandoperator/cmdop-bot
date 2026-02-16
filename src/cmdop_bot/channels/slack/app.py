"""Slack app implementation using slack-bolt."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from cmdop_bot.core.base import BaseChannel
from cmdop_bot.core.permissions import PermissionManager
from cmdop_bot.channels.slack.blocks import BlockBuilder

if TYPE_CHECKING:
    from cmdop import AsyncCMDOPClient

logger = logging.getLogger(__name__)


class SlackApp(BaseChannel):
    """Slack app using slack-bolt with CMDOP SDK integration.

    Uses Socket Mode for real-time events without public webhooks.

    Example:
        >>> app = SlackApp(
        ...     bot_token="xoxb-YOUR-BOT-TOKEN",
        ...     app_token="xapp-YOUR-APP-TOKEN",
        ...     cmdop_api_key="cmd_xxx",
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
            timeout: Default command timeout in seconds.
        """
        super().__init__(bot_token, cmdop_api_key)
        self._app_token = app_token
        self._allowed_users = set(allowed_users) if allowed_users else None
        self._permissions = permissions or PermissionManager()
        self._machine = machine
        self._timeout = timeout

        self._app: Any = None
        self._handler: Any = None
        self._cmdop_client: AsyncCMDOPClient | None = None

    @property
    def name(self) -> str:
        return "slack"

    async def _get_cmdop_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client (lazy initialization)."""
        if self._cmdop_client is None:
            from cmdop import AsyncCMDOPClient

            self._cmdop_client = AsyncCMDOPClient.remote(api_key=self._cmdop_api_key)

            if self._machine:
                await self._cmdop_client.terminal.set_machine(self._machine)
                logger.info(f"Connected to machine: {self._machine}")

        return self._cmdop_client

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
            client = await self._get_cmdop_client()

            output, exit_code = await client.terminal.execute(
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
            client = await self._get_cmdop_client()

            result = await client.agent.run(task)

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
            client = await self._get_cmdop_client()
            session = await client.terminal.set_machine(hostname)

            blocks = BlockBuilder.machine_info(
                hostname=session.machine_hostname,
                os=session.os,
                shell=session.shell,
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
            client = await self._get_cmdop_client()

            fields = [
                ("Mode", client.mode),
                ("Connected", ":white_check_mark: Yes" if client.is_connected else ":x: No"),
            ]

            current_session = client.terminal.current_session
            if current_session:
                fields.append(("Machine", f"`{current_session.machine_hostname}`"))

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
            client = await self._get_cmdop_client()
            response = await client.files.list(path)
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
            client = await self._get_cmdop_client()
            content = await client.files.read(path)

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
        if self._cmdop_client:
            await self._cmdop_client.close()
            self._cmdop_client = None
        logger.info("Slack app stopped")

    async def send(self, chat_id: str, text: str) -> None:
        """Send message to channel."""
        if self._app:
            await self._app.client.chat_postMessage(channel=chat_id, text=text)
