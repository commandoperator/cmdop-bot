"""Discord embed builders."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import discord


class EmbedBuilder:
    """Build Discord embeds for CMDOP responses."""

    # Colors
    COLOR_SUCCESS = 0x00FF00  # Green
    COLOR_ERROR = 0xFF0000  # Red
    COLOR_WARNING = 0xFFA500  # Orange
    COLOR_INFO = 0x0099FF  # Blue
    COLOR_CMDOP = 0x7C3AED  # Purple (CMDOP brand)

    @classmethod
    def success(cls, title: str, description: str) -> discord.Embed:
        """Create success embed."""
        import discord

        return discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=cls.COLOR_SUCCESS,
        )

    @classmethod
    def error(cls, title: str, description: str) -> discord.Embed:
        """Create error embed."""
        import discord

        return discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=cls.COLOR_ERROR,
        )

    @classmethod
    def warning(cls, title: str, description: str) -> discord.Embed:
        """Create warning embed."""
        import discord

        return discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=cls.COLOR_WARNING,
        )

    @classmethod
    def info(cls, title: str, description: str) -> discord.Embed:
        """Create info embed."""
        import discord

        return discord.Embed(
            title=title,
            description=description,
            color=cls.COLOR_INFO,
        )

    @classmethod
    def code_output(
        cls,
        command: str,
        output: str,
        exit_code: int,
        *,
        truncated: bool = False,
    ) -> discord.Embed:
        """Create code output embed."""
        import discord

        if exit_code == 0:
            color = cls.COLOR_SUCCESS
            title = "Command Executed"
        elif exit_code == -1:
            color = cls.COLOR_WARNING
            title = "Command Timeout"
        else:
            color = cls.COLOR_ERROR
            title = f"Command Failed (exit {exit_code})"

        embed = discord.Embed(
            title=title,
            color=color,
        )

        # Command field
        embed.add_field(
            name="Command",
            value=f"```bash\n{command[:200]}```",
            inline=False,
        )

        # Output field (truncate for Discord limits)
        if len(output) > 1000:
            output = output[:1000] + "\n... (truncated)"
            truncated = True

        if output.strip():
            embed.add_field(
                name="Output",
                value=f"```\n{output}\n```",
                inline=False,
            )

        if truncated:
            embed.set_footer(text="Output was truncated due to length limits")

        return embed

    @classmethod
    def machine_info(
        cls,
        hostname: str,
        os: str | None = None,
        shell: str | None = None,
    ) -> discord.Embed:
        """Create machine info embed."""
        import discord

        embed = discord.Embed(
            title="🖥️ Machine Connected",
            color=cls.COLOR_CMDOP,
        )

        embed.add_field(name="Hostname", value=f"`{hostname}`", inline=True)
        if os:
            embed.add_field(name="OS", value=os, inline=True)
        if shell:
            embed.add_field(name="Shell", value=shell, inline=True)

        return embed

    @classmethod
    def agent_result(
        cls,
        task: str,
        result: str,
        success: bool,
    ) -> discord.Embed:
        """Create agent result embed."""
        import discord

        color = cls.COLOR_SUCCESS if success else cls.COLOR_ERROR
        title = "🤖 Agent Result" if success else "🤖 Agent Error"

        embed = discord.Embed(
            title=title,
            color=color,
        )

        embed.add_field(
            name="Task",
            value=task[:200] if len(task) > 200 else task,
            inline=False,
        )

        # Truncate result for Discord limits
        if len(result) > 1800:
            result = result[:1800] + "\n... (truncated)"

        embed.add_field(
            name="Result",
            value=result,
            inline=False,
        )

        return embed

    @classmethod
    def help_embed(cls) -> discord.Embed:
        """Create help embed."""
        import discord

        embed = discord.Embed(
            title="CMDOP Bot Commands",
            description="Control your servers via Discord",
            color=cls.COLOR_CMDOP,
        )

        commands = [
            ("`/shell <command>`", "Execute shell command"),
            ("`/agent <task>`", "Run AI agent task"),
            ("`/ls [path]`", "List directory contents"),
            ("`/cat <path>`", "Read file contents"),
            ("`/machine <hostname>`", "Set target machine"),
            ("`/status`", "Show connection status"),
        ]

        for name, desc in commands:
            embed.add_field(name=name, value=desc, inline=False)

        embed.set_footer(text="CMDOP - Remote Machine Access")

        return embed

    @classmethod
    def file_list(
        cls,
        path: str,
        entries: list,
    ) -> discord.Embed:
        """Create file list embed."""
        import discord

        embed = discord.Embed(
            title=f"📁 {path}",
            color=cls.COLOR_CMDOP,
        )

        if not entries:
            embed.description = "Directory is empty"
            return embed

        lines = []
        for entry in entries[:25]:  # Limit for embed
            if entry.type.value == "directory":
                lines.append(f"📂 `{entry.name}/`")
            else:
                size = cls._format_size(entry.size)
                lines.append(f"📄 `{entry.name}` ({size})")

        embed.description = "\n".join(lines)

        if len(entries) > 25:
            embed.set_footer(text=f"Showing 25 of {len(entries)} entries")

        return embed

    @classmethod
    def file_content(
        cls,
        path: str,
        content: str,
    ) -> discord.Embed:
        """Create file content embed."""
        import discord
        import os

        file_name = os.path.basename(path) or path

        embed = discord.Embed(
            title=f"📄 {file_name}",
            color=cls.COLOR_CMDOP,
        )

        # Truncate content for Discord limits
        truncated = False
        if len(content) > 1800:
            content = content[:1800]
            truncated = True

        embed.description = f"```\n{content}\n```"

        if truncated:
            embed.set_footer(text="Content truncated due to length limits")

        return embed

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
