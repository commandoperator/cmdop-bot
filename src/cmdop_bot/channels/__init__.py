"""Channel implementations for CMDOP SDK.

Available channels:
- telegram: Telegram bot via aiogram
- discord: Discord bot via discord.py
- slack: Slack app via slack-bolt
- demo: CLI bot for local testing (no external deps)
"""

# Lazy imports to avoid requiring all channel dependencies
__all__ = ["telegram", "discord", "slack", "demo"]


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
    elif name == "demo":
        from cmdop_bot.channels import demo
        return demo
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
