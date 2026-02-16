"""Channel implementations for CMDOP SDK.

Available channels:
- telegram: Telegram bot via aiogram
- discord: Discord bot via discord.py
- slack: Slack app via slack-bolt
"""

# Lazy imports to avoid requiring all channel dependencies
__all__ = ["telegram", "discord", "slack"]


def __getattr__(name: str):
    """Lazy-load channel modules."""
    if name == "telegram":
        from cmdop_bot.channels import telegram
        return telegram
    elif name == "discord":
        from cmdop_bot.channels import discord
        return discord
    elif name == "slack":
        from cmdop_bot.channels import slack
        return slack
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
