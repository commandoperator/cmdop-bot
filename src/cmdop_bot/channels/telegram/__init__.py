"""Telegram bot integration.

Example:
    >>> from cmdop_bot.channels.telegram import TelegramBot
    >>> bot = TelegramBot(token="123:ABC", cmdop_api_key="cmd_xxx")
    >>> bot.run()
"""

from cmdop_bot.channels.telegram.bot import TelegramBot

__all__ = ["TelegramBot"]
