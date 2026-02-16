"""Help command handler."""

from cmdop_bot.core.handler import MessageHandler, SendCallback
from cmdop_bot.models import Command


class HelpHandler(MessageHandler):
    """Handle /help command - show available commands."""

    def __init__(self, handlers: list[MessageHandler] | None = None) -> None:
        """Initialize handler.

        Args:
            handlers: List of other handlers to include in help.
        """
        self._handlers = handlers or []

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "Show available commands"

    def add_handler(self, handler: MessageHandler) -> None:
        """Add handler to help list."""
        self._handlers.append(handler)

    async def handle(self, command: Command, send: SendCallback) -> None:
        """Show help message."""
        lines = ["**Available Commands:**\n"]

        # Add self
        lines.append(f"• `/help` - {self.description}")

        # Add other handlers
        for handler in self._handlers:
            lines.append(f"• `/{handler.name}` - {handler.description}")

        await send("\n".join(lines))
