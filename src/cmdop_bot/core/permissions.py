"""Permission manager."""

import json
from pathlib import Path
from typing import Dict

from cmdop_bot.models import Permission, PermissionLevel
from cmdop_bot.exceptions import PermissionDeniedError


class PermissionManager:
    """Manage user permissions.

    Example:
        >>> pm = PermissionManager()
        >>> pm.grant("telegram:123", "prod-server", PermissionLevel.EXECUTE)
        >>> pm.check("telegram:123", "prod-server", "shell")
        True
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize permission manager.

        Args:
            storage_path: Path to JSON file for persistence. None for in-memory only.
        """
        self._storage_path = storage_path
        self._permissions: Dict[str, Permission] = {}
        self._admins: set[str] = set()

        if storage_path and storage_path.exists():
            self._load()

    def grant(
        self,
        user_id: str,
        machine: str = "*",
        level: PermissionLevel = PermissionLevel.EXECUTE,
    ) -> None:
        """Grant permission to user."""
        key = f"{user_id}:{machine}"
        self._permissions[key] = Permission(
            user_id=user_id,
            machine=machine,
            level=level,
        )
        self._save()

    def revoke(self, user_id: str, machine: str = "*") -> None:
        """Revoke permission from user."""
        key = f"{user_id}:{machine}"
        self._permissions.pop(key, None)
        self._save()

    def add_admin(self, user_id: str) -> None:
        """Add user as admin (all permissions)."""
        self._admins.add(user_id)
        self._save()

    def remove_admin(self, user_id: str) -> None:
        """Remove admin status."""
        self._admins.discard(user_id)
        self._save()

    def is_admin(self, user_id: str) -> bool:
        """Check if user is admin."""
        return user_id in self._admins

    def check(self, user_id: str, machine: str, command: str) -> bool:
        """Check if user can execute command on machine."""
        if self.is_admin(user_id):
            return True

        # Check specific machine permission
        key = f"{user_id}:{machine}"
        perm = self._permissions.get(key)
        if perm and perm.can_execute(command):
            return True

        # Check wildcard permission
        key = f"{user_id}:*"
        perm = self._permissions.get(key)
        if perm and perm.can_execute(command):
            return True

        return False

    def require(self, user_id: str, machine: str, command: str) -> None:
        """Check permission or raise PermissionDeniedError."""
        if not self.check(user_id, machine, command):
            raise PermissionDeniedError(user_id, command, machine=machine)

    def get_permission(self, user_id: str, machine: str) -> Permission | None:
        """Get user's permission for machine."""
        key = f"{user_id}:{machine}"
        return self._permissions.get(key)

    def _save(self) -> None:
        """Save to JSON file."""
        if not self._storage_path:
            return

        data = {
            "admins": list(self._admins),
            "permissions": {k: v.model_dump() for k, v in self._permissions.items()},
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _load(self) -> None:
        """Load from JSON file."""
        if not self._storage_path or not self._storage_path.exists():
            return

        data = json.loads(self._storage_path.read_text())
        self._admins = set(data.get("admins", []))
        self._permissions = {
            k: Permission.model_validate(v)
            for k, v in data.get("permissions", {}).items()
        }
