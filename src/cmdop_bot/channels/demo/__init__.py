"""Demo channel - CLI bot for local testing.

Same handlers as Telegram/Discord but runs in terminal.
No external API dependencies - just rich for formatting.
"""

from cmdop_bot.channels.demo.bot import DemoBot

__all__ = ["DemoBot"]
