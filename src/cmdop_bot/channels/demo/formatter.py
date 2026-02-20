"""CLI formatter using Rich."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text


class DemoFormatter:
    """Formatter for CLI output using Rich."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def escape(self, text: str) -> str:
        """No escaping needed for CLI."""
        return text

    def error(self, text: str) -> str:
        """Format error message."""
        return f"[red]Error:[/red] {text}"

    def success(self, text: str) -> str:
        """Format success message."""
        return f"[green]{text}[/green]"

    def warning(self, text: str) -> str:
        """Format warning message."""
        return f"[yellow]{text}[/yellow]"

    def code(self, text: str, language: str = "") -> str:
        """Format code block."""
        return f"```{language}\n{text}\n```"

    def bold(self, text: str) -> str:
        """Format bold text."""
        return f"[bold]{text}[/bold]"

    def print_message(self, text: str, *, sender: str = "Bot") -> None:
        """Print a message with sender prefix."""
        self.console.print(f"[bold cyan]{sender}:[/bold cyan] {text}")

    def print_thinking(self) -> None:
        """Print thinking indicator."""
        self.console.print("[dim]Thinking...[/dim]")

    def print_result(self, text: str, *, title: str = "Result") -> None:
        """Print result in a panel."""
        # Try to render as markdown if it looks like markdown
        if "```" in text or text.startswith("#") or "**" in text:
            content = Markdown(text)
        else:
            content = Text(text)

        self.console.print(Panel(content, title=title, border_style="green"))

    def print_error(self, text: str) -> None:
        """Print error in a panel."""
        self.console.print(Panel(text, title="Error", border_style="red"))

    def print_help(self, commands: list[tuple[str, str]]) -> None:
        """Print help with command list."""
        self.console.print("\n[bold]Available Commands:[/bold]\n")
        for cmd, desc in commands:
            self.console.print(f"  [cyan]{cmd:20}[/cyan] {desc}")
        self.console.print()

    def print_status(self, machine: str | None, model: str | None) -> None:
        """Print current status."""
        self.console.print("\n[bold]Current Status:[/bold]")
        self.console.print(f"  Machine: [cyan]{machine or '(not set)'}[/cyan]")
        self.console.print(f"  Model:   [cyan]{model or '(default)'}[/cyan]")
        self.console.print()
