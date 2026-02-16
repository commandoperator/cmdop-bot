"""Tests for permission manager."""

import pytest

from cmdop_bot.core.permissions import PermissionManager
from cmdop_bot.models import PermissionLevel
from cmdop_bot.exceptions import PermissionDeniedError


class TestPermissionManager:
    """Tests for PermissionManager."""

    def test_add_admin(self):
        """Test adding an admin."""
        pm = PermissionManager()
        pm.add_admin("telegram:123")

        assert pm.is_admin("telegram:123")
        assert not pm.is_admin("telegram:456")

    def test_grant_permission(self):
        """Test granting permission."""
        pm = PermissionManager()
        pm.grant("telegram:123", machine="server1", level=PermissionLevel.EXECUTE)

        assert pm.check("telegram:123", "server1", "shell")

    def test_revoke_permission(self):
        """Test revoking permission."""
        pm = PermissionManager()
        pm.grant("telegram:123", machine="server1", level=PermissionLevel.EXECUTE)
        pm.revoke("telegram:123", machine="server1")

        assert not pm.check("telegram:123", "server1", "shell")

    def test_wildcard_machine(self):
        """Test wildcard machine permission."""
        pm = PermissionManager()
        pm.grant("telegram:123", machine="*", level=PermissionLevel.EXECUTE)

        assert pm.check("telegram:123", "any-server", "shell")

    def test_admin_has_all_access(self):
        """Test that admin has access to everything."""
        pm = PermissionManager()
        pm.add_admin("telegram:123")

        assert pm.check("telegram:123", "any-server", "shell")
        assert pm.check("telegram:123", "another-server", "files")

    def test_get_permission(self):
        """Test getting permission object."""
        pm = PermissionManager()
        pm.grant("telegram:123", machine="server1", level=PermissionLevel.FILES)

        perm = pm.get_permission("telegram:123", "server1")
        assert perm is not None
        assert perm.level == PermissionLevel.FILES

    def test_no_permission_returns_none(self):
        """Test that no permission returns None."""
        pm = PermissionManager()

        perm = pm.get_permission("telegram:unknown", "server1")
        assert perm is None

    def test_insufficient_permission(self):
        """Test that insufficient permission denies access."""
        pm = PermissionManager()
        pm.grant("telegram:123", machine="server1", level=PermissionLevel.READ)

        # Read level should not allow execute
        assert not pm.check("telegram:123", "server1", "shell")

    def test_require_raises_on_failure(self):
        """Test that require raises PermissionDeniedError."""
        pm = PermissionManager()

        with pytest.raises(PermissionDeniedError):
            pm.require("telegram:123", "server1", "shell")

    def test_require_passes_for_admin(self):
        """Test that require passes for admin."""
        pm = PermissionManager()
        pm.add_admin("telegram:123")

        # Should not raise
        pm.require("telegram:123", "server1", "shell")

    def test_remove_admin(self):
        """Test removing admin status."""
        pm = PermissionManager()
        pm.add_admin("telegram:123")
        pm.remove_admin("telegram:123")

        assert not pm.is_admin("telegram:123")
