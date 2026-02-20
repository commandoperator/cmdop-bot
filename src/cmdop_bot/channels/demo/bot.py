"""Demo bot - CLI interface for testing bot commands."""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Prompt

from cmdop_bot.core.base import BaseChannel
from cmdop_bot.core.cmdop_handler import CMDOPHandler
from cmdop_bot.channels.demo.formatter import DemoFormatter
from cmdop_bot.models import User, Message, Command

if TYPE_CHECKING:
    from cmdop.models.agent import AgentStreamEvent

logger = logging.getLogger(__name__)


class DemoBot(BaseChannel):
    """CLI bot for local testing - same logic as Telegram/Discord.

    Example:
        >>> from cmdop_bot.channels.demo import DemoBot
        >>>
        >>> bot = DemoBot(
        ...     cmdop_api_key="cmd_xxx",
        ...     machine="my-server",
        ...     model="@balanced+agents",
        ... )
        >>> bot.run()
    """

    COMMANDS = [
        ("/help", "Show this help"),
        ("/agent <task>", "Run AI agent with task"),
        ("/shell <cmd>", "Execute shell command"),
        ("/exec <cmd>", "Alias for /shell"),
        ("/ls [path]", "List directory"),
        ("/cat <file>", "Read file contents"),
        ("/machine [name]", "Set or show target machine"),
        ("/status", "Show current status"),
        ("/quit", "Exit the bot"),
    ]

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
        model: str | None = None,
        server: str | None = None,
        insecure: bool = False,
        timeout: float = 120.0,
        stream: bool = True,
    ) -> None:
        """Initialize Demo bot.

        Args:
            cmdop_api_key: CMDOP API key
            machine: Target machine hostname
            model: LLM model alias
            server: gRPC server address (e.g., "127.0.0.1:50051")
            insecure: Use insecure connection (no TLS)
            timeout: Default command timeout
            stream: Use streaming for agent responses
        """
        # No token needed for demo
        super().__init__("demo", cmdop_api_key)

        self._timeout = timeout
        self._stream = stream
        self._console = Console()
        self._formatter = DemoFormatter(self._console)

        # CMDOP handler
        self._cmdop = CMDOPHandler(
            api_key=cmdop_api_key,
            machine=machine,
            model=model,
            server=server,
            insecure=insecure,
        )

        self._input_task: asyncio.Task | None = None

    @property
    def name(self) -> str:
        return "demo"

    async def start(self) -> None:
        """Start the bot - begin input loop."""
        self._running = True

        # Print welcome
        self._console.print("\n[bold green]CMDOP Demo Bot[/bold green]")
        self._console.print("Type [cyan]/help[/cyan] for available commands\n")

        # Show status
        self._formatter.print_status(self._cmdop.machine, self._cmdop.model)

        # Start input loop in background
        self._input_task = asyncio.create_task(self._input_loop())

    async def stop(self) -> None:
        """Stop the bot."""
        self._running = False

        if self._input_task and not self._input_task.done():
            self._input_task.cancel()
            try:
                await self._input_task
            except asyncio.CancelledError:
                pass

        await self._cmdop.close()
        self._console.print("\n[dim]Goodbye![/dim]")

    async def send(self, chat_id: str, text: str) -> None:
        """Send message (print to console)."""
        self._formatter.print_message(text)

    async def send_typing(self, chat_id: str) -> None:
        """Show typing indicator."""
        self._formatter.print_thinking()

    async def _input_loop(self) -> None:
        """Main input loop."""
        while self._running:
            try:
                # Get input in thread to not block event loop
                text = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: Prompt.ask("[bold]You[/bold]"),
                )

                if not text:
                    continue

                await self._handle_input(text)

            except (KeyboardInterrupt, EOFError):
                self._running = False
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in input loop")
                self._formatter.print_error(str(e))

    async def _handle_input(self, text: str) -> None:
        """Handle user input."""
        text = text.strip()

        if not text:
            return

        # Parse command
        if text.startswith("/"):
            command = Command.parse_text(text)
            if command:
                await self._handle_command(command)
            else:
                self._formatter.print_error(f"Unknown command: {text}")
        else:
            # Treat as agent prompt
            await self._handle_agent(text)

    async def _handle_command(self, cmd: Command) -> None:
        """Handle a parsed command."""
        name = cmd.name.lower()

        if name == "help":
            self._formatter.print_help(self.COMMANDS)

        elif name == "quit" or name == "exit":
            self._running = False

        elif name == "status":
            self._formatter.print_status(self._cmdop.machine, self._cmdop.model)

        elif name == "agent":
            if cmd.args_text:
                await self._handle_agent(cmd.args_text)
            else:
                self._console.print("[yellow]Usage: /agent <task>[/yellow]")

        elif name in ("shell", "exec"):
            if cmd.args_text:
                await self._handle_shell(cmd.args_text)
            else:
                self._console.print("[yellow]Usage: /shell <command>[/yellow]")

        elif name == "ls":
            path = cmd.args_text or "."
            await self._handle_ls(path)

        elif name == "cat":
            if cmd.args_text:
                await self._handle_cat(cmd.args_text)
            else:
                self._console.print("[yellow]Usage: /cat <file>[/yellow]")

        elif name == "machine":
            if cmd.args_text:
                await self._handle_set_machine(cmd.args_text)
            else:
                machine = self._cmdop.machine or "(not set)"
                self._console.print(f"Current machine: [cyan]{machine}[/cyan]")

        else:
            self._formatter.print_error(f"Unknown command: /{name}")

    async def _handle_agent(self, prompt: str) -> None:
        """Handle agent task."""
        self._formatter.print_thinking()

        try:
            if self._stream:
                # Streaming mode
                tokens: list[str] = []

                async def on_event(event: AgentStreamEvent) -> None:
                    if event.type == "token":
                        token = event.payload
                        tokens.append(token)
                        # Print token without newline
                        self._console.print(token, end="")
                    elif event.type == "tool_start":
                        tool_name = event.payload.get("tool_name", "unknown")
                        self._console.print(f"\n[dim]Using tool: {tool_name}[/dim]")
                    elif event.type == "tool_end":
                        pass  # Tool finished

                self._console.print()  # Start new line for tokens
                result = await self._cmdop.run_agent_stream(prompt, on_event=on_event)
                self._console.print()  # End line after tokens

                if result.success:
                    if not tokens:
                        # No streaming tokens, show result text
                        self._formatter.print_result(result.text or "Done", title="Agent")
                else:
                    self._formatter.print_error(result.error or "Agent failed")
            else:
                # Non-streaming mode
                result = await self._cmdop.run_agent(prompt)

                if result.success:
                    self._formatter.print_result(result.text or "Done", title="Agent")
                else:
                    self._formatter.print_error(result.error or "Agent failed")

        except Exception as e:
            logger.exception("Agent failed")
            self._formatter.print_error(str(e))

    async def _handle_shell(self, command: str) -> None:
        """Handle shell command."""
        self._formatter.print_thinking()

        try:
            output, exit_code = await self._cmdop.execute_shell(
                command, timeout=self._timeout
            )

            decoded = output.decode("utf-8", errors="replace")

            if exit_code == 0:
                self._formatter.print_result(decoded, title=f"Shell (exit {exit_code})")
            else:
                self._console.print(
                    f"[yellow]Exit code: {exit_code}[/yellow]\n{decoded}"
                )

        except Exception as e:
            logger.exception("Shell failed")
            self._formatter.print_error(str(e))

    async def _handle_ls(self, path: str) -> None:
        """Handle ls command."""
        try:
            result = await self._cmdop.list_files(path)

            lines = []
            for entry in result.entries:
                icon = "[bold blue]" if entry.is_dir else ""
                suffix = "/" if entry.is_dir else ""
                lines.append(f"{icon}{entry.name}{suffix}")

            self._formatter.print_result("\n".join(lines), title=f"ls {path}")

        except Exception as e:
            logger.exception("ls failed")
            self._formatter.print_error(str(e))

    async def _handle_cat(self, path: str) -> None:
        """Handle cat command."""
        try:
            content = await self._cmdop.read_file(path)
            decoded = content.decode("utf-8", errors="replace")

            # Truncate if too long
            if len(decoded) > 5000:
                decoded = decoded[:5000] + "\n... (truncated)"

            self._formatter.print_result(decoded, title=f"cat {path}")

        except Exception as e:
            logger.exception("cat failed")
            self._formatter.print_error(str(e))

    async def _handle_set_machine(self, hostname: str) -> None:
        """Handle machine set command."""
        try:
            full_hostname = await self._cmdop.set_machine(hostname)
            self._console.print(f"[green]Connected to:[/green] {full_hostname}")
        except Exception as e:
            logger.exception("set_machine failed")
            self._formatter.print_error(str(e))
