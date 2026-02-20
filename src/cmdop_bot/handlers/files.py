"""Files command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.core.handler import MessageHandler, SendCallback
from cmdop_bot.models import Command

if TYPE_CHECKING:
    from cmdop import AsyncCMDOPClient

logger = logging.getLogger(__name__)


class FilesHandler(MessageHandler):
    """Handle /files, /ls, /cat commands - file operations via CMDOP.

    Example:
        >>> handler = FilesHandler(cmdop_api_key="cmd_xxx")
        >>> await handler.handle(command, send)
    """

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
    ) -> None:
        """Initialize handler.

        Args:
            cmdop_api_key: CMDOP API key (cmd_xxx format)
            machine: Target machine hostname. None = use default.
        """
        self._api_key = cmdop_api_key
        self._machine = machine
        self._client: AsyncCMDOPClient | None = None

    @property
    def name(self) -> str:
        return "files"

    @property
    def description(self) -> str:
        return "List and read files on remote machine"

    async def _get_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client."""
        if self._client is None:
            from cmdop import AsyncCMDOPClient

            self._client = AsyncCMDOPClient.remote(api_key=self._api_key)

            if self._machine:
                # Set machine for files service (not terminal!)
                await self._client.files.set_machine(self._machine)

        return self._client

    async def handle(self, command: Command, send: SendCallback) -> None:
        """Handle file commands."""
        # Parse subcommand: /files ls /path or /files cat /path
        args = command.args

        if not args:
            await send(
                "Usage:\n"
                "  /files ls [path] - List directory\n"
                "  /files cat <path> - Read file\n"
                "  /files info <path> - File info"
            )
            return

        subcommand = args[0].lower()
        path = args[1] if len(args) > 1 else "."

        try:
            client = await self._get_client()

            if subcommand == "ls" or subcommand == "list":
                await self._handle_list(client, path, send)
            elif subcommand == "cat" or subcommand == "read":
                await self._handle_read(client, path, send)
            elif subcommand == "info":
                await self._handle_info(client, path, send)
            else:
                await send(f"Unknown subcommand: {subcommand}")

        except Exception as e:
            logger.exception("File operation failed")
            await send(f"Error: {e}")

    async def _handle_list(
        self,
        client: AsyncCMDOPClient,
        path: str,
        send: SendCallback,
    ) -> None:
        """List directory contents."""
        response = await client.files.list(path)
        entries = response.entries

        if not entries:
            await send(f"Directory is empty: {path}")
            return

        lines = [f"📁 {path}\n"]
        for entry in entries[:50]:  # Limit to 50 entries
            if entry.type.value == "directory":
                lines.append(f"  📂 {entry.name}/")
            else:
                size = self._format_size(entry.size)
                lines.append(f"  📄 {entry.name} ({size})")

        if len(entries) > 50:
            lines.append(f"\n... and {len(entries) - 50} more")

        await send("\n".join(lines))

    async def _handle_read(
        self,
        client: AsyncCMDOPClient,
        path: str,
        send: SendCallback,
    ) -> None:
        """Read file contents."""
        content = await client.files.read(path)

        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError:
                await send(f"Binary file: {path} ({len(content)} bytes)")
                return

        # Truncate long files
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"

        await send(f"```\n{content}\n```")

    async def _handle_info(
        self,
        client: AsyncCMDOPClient,
        path: str,
        send: SendCallback,
    ) -> None:
        """Get file info."""
        import os
        info = await client.files.info(path)

        # Extract name from path
        file_name = os.path.basename(info.path) or info.path
        is_dir = info.type.value == "directory"

        lines = [
            f"📄 {file_name}",
            f"Path: {info.path}",
            f"Size: {self._format_size(info.size)}",
            f"Type: {'Directory' if is_dir else 'File'}",
        ]

        if info.modified_at:
            lines.append(f"Modified: {info.modified_at}")

        if info.permissions:
            lines.append(f"Permissions: {info.permissions}")

        await send("\n".join(lines))

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size for display."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

    async def close(self) -> None:
        """Close CMDOP client."""
        if self._client is not None:
            await self._client.close()
            self._client = None


class LsHandler(MessageHandler):
    """Handle /ls command - shortcut for /files ls."""

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
    ) -> None:
        self._files_handler = FilesHandler(cmdop_api_key, machine=machine)

    @property
    def name(self) -> str:
        return "ls"

    @property
    def description(self) -> str:
        return "List directory contents"

    async def handle(self, command: Command, send: SendCallback) -> None:
        """List directory."""
        # Prepend "ls" to args for FilesHandler
        modified_command = Command(
            name="files",
            args=["ls"] + command.args,
            raw_text=command.raw_text,
            message=command.message,
        )
        await self._files_handler.handle(modified_command, send)

    async def close(self) -> None:
        await self._files_handler.close()


class CatHandler(MessageHandler):
    """Handle /cat command - shortcut for /files cat."""

    def __init__(
        self,
        cmdop_api_key: str,
        *,
        machine: str | None = None,
    ) -> None:
        self._files_handler = FilesHandler(cmdop_api_key, machine=machine)

    @property
    def name(self) -> str:
        return "cat"

    @property
    def description(self) -> str:
        return "Read file contents"

    async def handle(self, command: Command, send: SendCallback) -> None:
        """Read file."""
        if not command.args:
            await send("Usage: /cat <path>")
            return

        modified_command = Command(
            name="files",
            args=["cat"] + command.args,
            raw_text=command.raw_text,
            message=command.message,
        )
        await self._files_handler.handle(modified_command, send)

    async def close(self) -> None:
        await self._files_handler.close()
