"""Text escaping utilities."""

import re


def escape_markdown(text: str, version: int = 2) -> str:
    """Escape special characters for Markdown.

    Args:
        text: Text to escape
        version: Markdown version (1 or 2). Default is 2 (Telegram MarkdownV2).

    Returns:
        Escaped text
    """
    if version == 2:
        # Telegram MarkdownV2 special characters
        chars = r"_*[]()~`>#+-=|{}.!"
        return re.sub(f"([{re.escape(chars)}])", r"\\\1", text)
    else:
        # Basic Markdown (version 1)
        chars = r"*_`["
        return re.sub(f"([{re.escape(chars)}])", r"\\\1", text)


def escape_html(text: str) -> str:
    """Escape special characters for HTML."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def truncate(text: str, max_length: int = 4000, suffix: str = "...") -> str:
    """Truncate text to max length.

    Args:
        text: Text to truncate
        max_length: Maximum length (default 4000 for Telegram)
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
