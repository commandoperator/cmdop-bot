"""Message and Command models."""

from typing import Any
from pydantic import BaseModel, Field

from cmdop_bot.models.user import User


class Message(BaseModel):
    """Incoming message from any channel.

    Example:
        >>> msg = Message(
        ...     id="123", channel="telegram", chat_id="456",
        ...     user=User(id="789", channel="telegram"),
        ...     text="/shell ls -la"
        ... )
    """

    id: str = Field(..., description="Message ID")
    channel: str = Field(..., description="Channel name")
    chat_id: str = Field(..., description="Chat/conversation ID")
    user: User = Field(..., description="Message author")
    text: str = Field(..., description="Message text")
    reply_to: str | None = Field(default=None, description="Reply to message ID")
    raw: Any = Field(default=None, exclude=True, description="Raw platform event")


class Command(BaseModel):
    """Parsed command from a message.

    Example:
        >>> cmd = Command(name="shell", args=["ls", "-la"], raw_text="/shell ls -la")
        >>> cmd.args_text
        'ls -la'
    """

    name: str = Field(..., description="Command name without prefix")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    raw_text: str = Field(..., description="Original message text")
    message: Message | None = Field(default=None, description="Source message")

    @property
    def args_text(self) -> str:
        """Arguments as single string."""
        return " ".join(self.args)

    @classmethod
    def parse(cls, text: str, message: Message | None = None) -> "Command | None":
        """Parse command from text. Returns None if not a command."""
        text = text.strip()
        if not text.startswith("/"):
            return None

        parts = text[1:].split(maxsplit=1)
        name = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []

        return cls(name=name, args=args, raw_text=text, message=message)
