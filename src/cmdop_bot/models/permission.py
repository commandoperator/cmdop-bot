"""Permission models."""

from enum import IntEnum
from pydantic import BaseModel, Field


class PermissionLevel(IntEnum):
    """Permission levels for users."""

    NONE = 0
    READ = 10       # View status only
    EXECUTE = 20    # Run shell commands
    FILES = 30      # File operations
    ADMIN = 100     # Full access


class Permission(BaseModel):
    """User permission for a machine.

    Example:
        >>> perm = Permission(
        ...     user_id="telegram:123456",
        ...     machine="prod-server",
        ...     level=PermissionLevel.EXECUTE
        ... )
    """

    user_id: str = Field(..., description="Unique user ID (channel:id)")
    machine: str = Field(default="*", description="Machine hostname or '*' for all")
    level: PermissionLevel = Field(
        default=PermissionLevel.NONE,
        description="Permission level"
    )
    allowed_commands: list[str] | None = Field(
        default=None,
        description="Allowed commands (None = all)"
    )
    denied_commands: list[str] | None = Field(
        default=None,
        description="Denied commands"
    )

    def can_execute(self, command: str) -> bool:
        """Check if user can execute the command."""
        if self.level < PermissionLevel.EXECUTE:
            return False

        if self.denied_commands and command in self.denied_commands:
            return False

        if self.allowed_commands is not None:
            return command in self.allowed_commands

        return True
