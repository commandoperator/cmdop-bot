"""Tests for models."""

import pytest

from cmdop_bot.models import User, Message, Command, Permission, PermissionLevel


class TestUser:
    """Tests for User model."""

    def test_create_user(self):
        """Test creating a user."""
        user = User(
            id="123",
            channel="telegram",
            username="testuser",
            display_name="Test User",
        )
        assert user.id == "123"
        assert user.channel == "telegram"
        assert user.username == "testuser"
        assert user.display_name == "Test User"

    def test_unique_id(self):
        """Test unique ID generation."""
        user = User(id="123", channel="telegram")
        assert user.unique_id == "telegram:123"

    def test_user_without_optional_fields(self):
        """Test creating user without optional fields."""
        user = User(id="456", channel="discord")
        assert user.id == "456"
        assert user.username is None
        assert user.display_name is None


class TestMessage:
    """Tests for Message model."""

    def test_create_message(self):
        """Test creating a message."""
        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="Hello world",
        )
        assert msg.id == "msg1"
        assert msg.text == "Hello world"
        assert msg.user.id == "123"


class TestCommand:
    """Tests for Command model."""

    def test_parse_command(self):
        """Test parsing a command from text."""
        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/shell ls -la",
        )
        cmd = Command.parse("/shell ls -la", msg)

        assert cmd is not None
        assert cmd.name == "shell"
        assert cmd.args == ["ls", "-la"]
        assert cmd.args_text == "ls -la"

    def test_parse_command_no_args(self):
        """Test parsing command without arguments."""
        user = User(id="123", channel="telegram")
        msg = Message(
            id="msg1",
            channel="telegram",
            chat_id="chat1",
            user=user,
            text="/help",
        )
        cmd = Command.parse("/help", msg)

        assert cmd is not None
        assert cmd.name == "help"
        assert cmd.args == []
        assert cmd.args_text == ""

    def test_parse_non_command(self):
        """Test parsing non-command text returns None."""
        cmd = Command.parse("Hello world")
        assert cmd is None


class TestPermission:
    """Tests for Permission model."""

    def test_permission_levels(self):
        """Test permission levels ordering."""
        assert PermissionLevel.NONE < PermissionLevel.READ
        assert PermissionLevel.READ < PermissionLevel.EXECUTE
        assert PermissionLevel.EXECUTE < PermissionLevel.FILES
        assert PermissionLevel.FILES < PermissionLevel.ADMIN

    def test_permission_can_execute(self):
        """Test permission execution check."""
        perm = Permission(
            user_id="telegram:123",
            machine="server1",
            level=PermissionLevel.EXECUTE,
        )
        assert perm.can_execute("shell")

    def test_permission_admin(self):
        """Test admin permission."""
        perm = Permission(
            user_id="telegram:123",
            machine="*",
            level=PermissionLevel.ADMIN,
        )
        assert perm.level == PermissionLevel.ADMIN
