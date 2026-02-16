"""User model."""

from pydantic import BaseModel, Field


class User(BaseModel):
    """User from any communication channel.

    Example:
        >>> user = User(id="123456", channel="telegram", username="john")
        >>> user.unique_id
        'telegram:123456'
    """

    id: str = Field(..., description="User ID within the channel")
    channel: str = Field(..., description="Channel name (telegram, discord, slack)")
    username: str | None = Field(default=None, description="Username/handle")
    display_name: str | None = Field(default=None, description="Display name")
    is_admin: bool = Field(default=False, description="Admin privileges")

    @property
    def unique_id(self) -> str:
        """Globally unique user identifier."""
        return f"{self.channel}:{self.id}"

    @property
    def name(self) -> str:
        """Best available name for display."""
        return self.display_name or self.username or self.id
