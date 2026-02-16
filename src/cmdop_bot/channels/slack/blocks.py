"""Slack Block Kit builders."""

from __future__ import annotations

from typing import Any


class BlockBuilder:
    """Build Slack Block Kit messages for CMDOP responses."""

    @staticmethod
    def text_section(text: str, *, markdown: bool = True) -> dict[str, Any]:
        """Create text section block."""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn" if markdown else "plain_text",
                "text": text,
            },
        }

    @staticmethod
    def code_block(code: str, title: str | None = None) -> list[dict[str, Any]]:
        """Create code block with optional title."""
        blocks: list[dict[str, Any]] = []

        if title:
            blocks.append(BlockBuilder.text_section(f"*{title}*"))

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```{code}```",
            },
        })

        return blocks

    @staticmethod
    def divider() -> dict[str, Any]:
        """Create divider block."""
        return {"type": "divider"}

    @staticmethod
    def header(text: str) -> dict[str, Any]:
        """Create header block."""
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True,
            },
        }

    @staticmethod
    def context(texts: list[str]) -> dict[str, Any]:
        """Create context block with multiple text elements."""
        return {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": t} for t in texts
            ],
        }

    @staticmethod
    def fields(field_pairs: list[tuple[str, str]]) -> dict[str, Any]:
        """Create section with fields (two-column layout)."""
        return {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*{label}*\n{value}"}
                for label, value in field_pairs
            ],
        }

    @staticmethod
    def button(
        text: str,
        action_id: str,
        *,
        value: str = "",
        style: str | None = None,
    ) -> dict[str, Any]:
        """Create button element."""
        btn: dict[str, Any] = {
            "type": "button",
            "text": {"type": "plain_text", "text": text, "emoji": True},
            "action_id": action_id,
            "value": value,
        }
        if style:
            btn["style"] = style  # "primary" or "danger"
        return btn

    @staticmethod
    def actions(buttons: list[dict[str, Any]]) -> dict[str, Any]:
        """Create actions block with buttons."""
        return {
            "type": "actions",
            "elements": buttons,
        }

    @classmethod
    def command_result(
        cls,
        command: str,
        output: str,
        exit_code: int,
    ) -> list[dict[str, Any]]:
        """Build command result message blocks."""
        blocks: list[dict[str, Any]] = []

        # Status header
        if exit_code == 0:
            status = ":white_check_mark: Command Executed"
        elif exit_code == -1:
            status = ":warning: Command Timeout"
        else:
            status = f":x: Command Failed (exit {exit_code})"

        blocks.append(cls.header(status))

        # Command
        blocks.append(cls.text_section(f"*Command:* `{command}`"))

        # Output
        if output.strip():
            # Truncate for Slack limits
            if len(output) > 2800:
                output = output[:2800] + "\n... (truncated)"
            blocks.extend(cls.code_block(output, title="Output"))

        return blocks

    @classmethod
    def machine_info(
        cls,
        hostname: str,
        os: str | None = None,
        shell: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build machine info message blocks."""
        blocks: list[dict[str, Any]] = []

        blocks.append(cls.header(":computer: Machine Connected"))

        fields = [("Hostname", f"`{hostname}`")]
        if os:
            fields.append(("OS", os))
        if shell:
            fields.append(("Shell", shell))

        blocks.append(cls.fields(fields))

        return blocks

    @classmethod
    def agent_result(
        cls,
        task: str,
        result: str,
        success: bool,
    ) -> list[dict[str, Any]]:
        """Build agent result message blocks."""
        blocks: list[dict[str, Any]] = []

        status = ":robot_face: Agent Result" if success else ":robot_face: Agent Error"
        blocks.append(cls.header(status))

        blocks.append(cls.text_section(f"*Task:* {task}"))
        blocks.append(cls.divider())

        # Truncate result
        if len(result) > 2800:
            result = result[:2800] + "\n... (truncated)"

        blocks.append(cls.text_section(result))

        return blocks

    @classmethod
    def help_message(cls) -> list[dict[str, Any]]:
        """Build help message blocks."""
        blocks: list[dict[str, Any]] = []

        blocks.append(cls.header("CMDOP Bot Commands"))

        commands_text = "\n".join([
            "`/cmdop shell <command>` - Execute shell command",
            "`/cmdop agent <task>` - Run AI agent task",
            "`/cmdop ls [path]` - List directory contents",
            "`/cmdop cat <path>` - Read file contents",
            "`/cmdop machine <hostname>` - Set target machine",
            "`/cmdop status` - Show connection status",
            "`/cmdop help` - Show this help",
        ])

        blocks.append(cls.text_section(commands_text))
        blocks.append(cls.context(["CMDOP - Remote Machine Access"]))

        return blocks

    @classmethod
    def error_message(cls, title: str, message: str) -> list[dict[str, Any]]:
        """Build error message blocks."""
        return [
            cls.header(f":x: {title}"),
            cls.text_section(message),
        ]

    @classmethod
    def file_list(cls, path: str, entries: list) -> list[dict[str, Any]]:
        """Build file list message blocks."""
        blocks: list[dict[str, Any]] = []

        blocks.append(cls.header(f":file_folder: {path}"))

        if not entries:
            blocks.append(cls.text_section("_Directory is empty_"))
            return blocks

        lines = []
        for entry in entries[:30]:  # Limit for Slack
            if entry.type.value == "directory":
                lines.append(f":file_folder: `{entry.name}/`")
            else:
                size = cls._format_size(entry.size)
                lines.append(f":page_facing_up: `{entry.name}` ({size})")

        blocks.append(cls.text_section("\n".join(lines)))

        if len(entries) > 30:
            blocks.append(cls.context([f"Showing 30 of {len(entries)} entries"]))

        return blocks

    @classmethod
    def file_content(cls, path: str, content: str) -> list[dict[str, Any]]:
        """Build file content message blocks."""
        import os

        blocks: list[dict[str, Any]] = []

        file_name = os.path.basename(path) or path
        blocks.append(cls.header(f":page_facing_up: {file_name}"))

        # Truncate for Slack limits
        truncated = False
        if len(content) > 2800:
            content = content[:2800]
            truncated = True

        blocks.extend(cls.code_block(content))

        if truncated:
            blocks.append(cls.context(["Content truncated due to length limits"]))

        return blocks

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
