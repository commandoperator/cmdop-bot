"""Tests for message formatters."""

import pytest


class TestTelegramFormatter:
    """Tests for Telegram formatter."""

    def test_escape_markdown(self):
        """Test MarkdownV2 escaping."""
        from cmdop_bot.channels.telegram.formatter import TelegramFormatter

        fmt = TelegramFormatter()

        # Test escaping special characters
        text = "Hello *world* [test]"
        escaped = fmt.escape(text)
        assert "\\*" in escaped
        assert "\\[" in escaped
        assert "\\]" in escaped

    def test_code_block(self):
        """Test code block formatting."""
        from cmdop_bot.channels.telegram.formatter import TelegramFormatter

        fmt = TelegramFormatter()

        code = "ls -la"
        result = fmt.code_block(code)
        assert result.startswith("```")
        assert result.endswith("```")
        assert code in result

    def test_code_block_with_language(self):
        """Test code block with language."""
        from cmdop_bot.channels.telegram.formatter import TelegramFormatter

        fmt = TelegramFormatter()

        code = "print('hello')"
        result = fmt.code_block(code, language="python")
        assert "```python" in result

    def test_error_formatting(self):
        """Test error message formatting."""
        from cmdop_bot.channels.telegram.formatter import TelegramFormatter

        fmt = TelegramFormatter()

        result = fmt.error("Something went wrong")
        assert "Error" in result

    def test_success_formatting(self):
        """Test success message formatting."""
        from cmdop_bot.channels.telegram.formatter import TelegramFormatter

        fmt = TelegramFormatter()

        result = fmt.success("Operation completed")
        assert "Operation completed" in result


class TestSlackBlockBuilder:
    """Tests for Slack Block Kit builder."""

    def test_text_section(self):
        """Test text section block."""
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        block = BlockBuilder.text_section("Hello world")
        assert block["type"] == "section"
        assert block["text"]["type"] == "mrkdwn"
        assert block["text"]["text"] == "Hello world"

    def test_code_block(self):
        """Test code block."""
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        blocks = BlockBuilder.code_block("ls -la", title="Output")
        assert len(blocks) == 2  # Title + code
        assert "```" in blocks[1]["text"]["text"]

    def test_header(self):
        """Test header block."""
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        block = BlockBuilder.header("Test Header")
        assert block["type"] == "header"
        assert block["text"]["text"] == "Test Header"

    def test_divider(self):
        """Test divider block."""
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        block = BlockBuilder.divider()
        assert block["type"] == "divider"

    def test_fields(self):
        """Test fields block."""
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        block = BlockBuilder.fields([
            ("Label1", "Value1"),
            ("Label2", "Value2"),
        ])
        assert block["type"] == "section"
        assert len(block["fields"]) == 2

    def test_command_result(self):
        """Test command result blocks."""
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        blocks = BlockBuilder.command_result(
            command="ls -la",
            output="file1\nfile2",
            exit_code=0,
        )
        assert len(blocks) >= 2  # Header + command + output


class TestDiscordEmbedBuilder:
    """Tests for Discord embed builder."""

    def test_success_embed(self):
        """Test success embed."""
        pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        embed = EmbedBuilder.success("Title", "Description")
        assert embed.color.value == EmbedBuilder.COLOR_SUCCESS

    def test_error_embed(self):
        """Test error embed."""
        pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        embed = EmbedBuilder.error("Title", "Description")
        assert embed.color.value == EmbedBuilder.COLOR_ERROR

    def test_code_output_embed(self):
        """Test code output embed."""
        pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        embed = EmbedBuilder.code_output(
            command="ls -la",
            output="file1\nfile2",
            exit_code=0,
        )
        assert len(embed.fields) >= 1
