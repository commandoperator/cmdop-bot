"""Telegram message formatter.

Handles MarkdownV2 escaping which is notoriously strict.
"""

import re


class TelegramFormatter:
    """Format messages for Telegram MarkdownV2.

    Telegram MarkdownV2 requires escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """

    # Characters that must be escaped in MarkdownV2
    ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!"

    def escape(self, text: str) -> str:
        """Escape special characters for MarkdownV2."""
        return re.sub(f"([{re.escape(self.ESCAPE_CHARS)}])", r"\\\1", text)

    def code_block(self, code: str, language: str = "") -> str:
        """Format code block.

        Note: Content inside code blocks doesn't need escaping except backticks.
        """
        # Replace triple backticks inside code to prevent breaking
        code = code.replace("```", "'''")
        return f"```{language}\n{code}\n```"

    def inline_code(self, code: str) -> str:
        """Format inline code."""
        code = code.replace("`", "'")
        return f"`{code}`"

    def bold(self, text: str) -> str:
        """Format bold text."""
        return f"*{self.escape(text)}*"

    def italic(self, text: str) -> str:
        """Format italic text."""
        return f"_{self.escape(text)}_"

    def error(self, message: str) -> str:
        """Format error message."""
        escaped = self.escape(message)
        return f"❌ *Error:* {escaped}"

    def success(self, message: str) -> str:
        """Format success message."""
        escaped = self.escape(message)
        return f"✅ {escaped}"

    def warning(self, message: str) -> str:
        """Format warning message."""
        escaped = self.escape(message)
        return f"⚠️ {escaped}"

    def progress(self, message: str) -> str:
        """Format progress message."""
        escaped = self.escape(message)
        return f"⏳ {escaped}"
