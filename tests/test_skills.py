"""Tests for skills handler integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cmdop_bot.models import User, Message, Command


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_skill_info(name="code-review", description="Review code", origin="workspace", author="team", version="1.0"):
    """Create a mock SkillInfo."""
    info = MagicMock()
    info.name = name
    info.description = description
    info.origin = origin
    info.author = author
    info.version = version
    info.model = ""
    info.required_bins = []
    info.required_env = []
    return info


def _make_skill_detail(*, found=True, name="code-review", content="You are a code reviewer.", source="/skills/code-review.md"):
    """Create a mock SkillDetail."""
    detail = MagicMock()
    detail.found = found
    detail.error = "" if found else f"Skill not found: {name}"
    if found:
        detail.info = _make_skill_info(name=name)
        detail.content = content
        detail.source = source
    else:
        detail.info = None
        detail.content = ""
        detail.source = ""
    return detail


def _make_skill_result(*, success=True, text="Review complete.", error="", duration_ms=1500):
    """Create a mock SkillRunResult."""
    result = MagicMock()
    result.success = success
    result.text = text
    result.error = error
    result.duration_ms = duration_ms
    result.duration_seconds = duration_ms / 1000.0
    return result


@pytest.fixture
def mock_cmdop_handler():
    """Mock CMDOPHandler with skills methods."""
    handler = AsyncMock()
    handler.machine = "test-server"
    handler.model = "@balanced+agents"

    handler.list_skills = AsyncMock(return_value=[
        _make_skill_info("code-review", "Review code changes", "workspace"),
        _make_skill_info("ssl-check", "Check SSL certificates", "builtin"),
    ])
    handler.show_skill = AsyncMock(return_value=_make_skill_detail())
    handler.run_skill = AsyncMock(return_value=_make_skill_result())
    handler.close = AsyncMock()

    return handler


# ---------------------------------------------------------------------------
# CMDOPHandler — skills methods
# ---------------------------------------------------------------------------

class TestCMDOPHandlerSkills:
    """Tests for CMDOPHandler skills methods."""

    @pytest.mark.asyncio
    async def test_list_skills(self, cmdop_api_key):
        """list_skills() delegates to client.skills.list()."""
        from cmdop_bot import CMDOPHandler

        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")
        mock_skills = [_make_skill_info()]

        with patch("cmdop.AsyncCMDOPClient") as cls:
            client = AsyncMock()
            client.skills.list = AsyncMock(return_value=mock_skills)
            cls.remote.return_value = client

            result = await handler.list_skills()

            client.skills.list.assert_called_once()
            assert result == mock_skills

    @pytest.mark.asyncio
    async def test_show_skill(self, cmdop_api_key):
        """show_skill() delegates to client.skills.show()."""
        from cmdop_bot import CMDOPHandler

        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")
        mock_detail = _make_skill_detail()

        with patch("cmdop.AsyncCMDOPClient") as cls:
            client = AsyncMock()
            client.skills.show = AsyncMock(return_value=mock_detail)
            cls.remote.return_value = client

            result = await handler.show_skill("code-review")

            client.skills.show.assert_called_once_with("code-review")
            assert result.found is True

    @pytest.mark.asyncio
    async def test_run_skill(self, cmdop_api_key):
        """run_skill() delegates to client.skills.run() with options."""
        from cmdop_bot import CMDOPHandler

        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")
        mock_result = _make_skill_result()

        with patch("cmdop.AsyncCMDOPClient") as cls:
            client = AsyncMock()
            client.skills.run = AsyncMock(return_value=mock_result)
            cls.remote.return_value = client

            with patch("cmdop.models.skills.SkillRunOptions") as opts_cls:
                opts = MagicMock()
                opts_cls.return_value = opts

                result = await handler.run_skill("code-review", "Review this PR")

                client.skills.run.assert_called_once()
                call_args = client.skills.run.call_args
                assert call_args[0][0] == "code-review"
                assert call_args[0][1] == "Review this PR"
                assert result.success is True

    @pytest.mark.asyncio
    async def test_run_skill_custom_timeout(self, cmdop_api_key):
        """run_skill() passes custom timeout to options."""
        from cmdop_bot import CMDOPHandler

        handler = CMDOPHandler(api_key=cmdop_api_key, machine="test-server")

        with patch("cmdop.AsyncCMDOPClient") as cls:
            client = AsyncMock()
            client.skills.run = AsyncMock(return_value=_make_skill_result())
            cls.remote.return_value = client

            with patch("cmdop.models.skills.SkillRunOptions") as opts_cls:
                await handler.run_skill("test", "prompt", timeout=120)
                opts_cls.assert_called_once_with(timeout_seconds=120)

    @pytest.mark.asyncio
    async def test_set_machine_includes_skills(self, cmdop_api_key):
        """set_machine() calls skills.set_machine() alongside other services."""
        from cmdop_bot import CMDOPHandler

        handler = CMDOPHandler(api_key=cmdop_api_key, machine="initial")
        mock_session = MagicMock()
        mock_session.machine_hostname = "full.local"

        with patch("cmdop.AsyncCMDOPClient") as cls:
            client = AsyncMock()
            client.terminal.set_machine = AsyncMock(return_value=mock_session)
            client.files.set_machine = AsyncMock()
            client.agent.set_machine = AsyncMock()
            client.skills.set_machine = AsyncMock()
            cls.remote.return_value = client

            await handler.set_machine("full")

            # Called twice: once during get_client() init ("initial"), once in set_machine("full")
            assert client.skills.set_machine.call_count == 2
            client.skills.set_machine.assert_called_with("full")

    @pytest.mark.asyncio
    async def test_get_client_sets_skills_machine(self, cmdop_api_key):
        """get_client() calls skills.set_machine() during init when machine is set."""
        from cmdop_bot import CMDOPHandler

        handler = CMDOPHandler(api_key=cmdop_api_key, machine="my-server")

        with patch("cmdop.AsyncCMDOPClient") as cls:
            client = AsyncMock()
            client.terminal.set_machine = AsyncMock()
            client.files.set_machine = AsyncMock()
            client.agent.set_machine = AsyncMock()
            client.skills.set_machine = AsyncMock()
            cls.remote.return_value = client

            await handler.get_client()

            client.skills.set_machine.assert_called_once_with("my-server")


# ---------------------------------------------------------------------------
# Generic SkillsHandler (channel-agnostic)
# ---------------------------------------------------------------------------

class TestGenericSkillsHandler:
    """Tests for handlers/skills.py SkillsHandler."""

    def test_name_and_description(self, cmdop_api_key):
        """Handler exposes correct name and description."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        assert h.name == "skills"
        assert h.description == "List, inspect, and run skills"

    @pytest.mark.asyncio
    async def test_no_args_shows_usage(self, cmdop_api_key):
        """No subcommand → usage message."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills")
        send = AsyncMock()

        await h.handle(cmd, send)

        send.assert_called_once()
        text = send.call_args[0][0]
        assert "/skills list" in text
        assert "/skills show" in text
        assert "/skills run" in text

    @pytest.mark.asyncio
    async def test_list_skills(self, cmdop_api_key):
        """list subcommand lists skills."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills list")
        send = AsyncMock()

        mock_skills = [_make_skill_info("ssl-check", "Check SSL", "builtin")]

        with patch.object(h, "_get_client") as gc:
            client = AsyncMock()
            client.skills.list = AsyncMock(return_value=mock_skills)
            gc.return_value = client

            await h.handle(cmd, send)

        send.assert_called_once()
        text = send.call_args[0][0]
        assert "ssl-check" in text
        assert "Check SSL" in text

    @pytest.mark.asyncio
    async def test_list_empty(self, cmdop_api_key):
        """list subcommand with no skills shows message."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills list")
        send = AsyncMock()

        with patch.object(h, "_get_client") as gc:
            client = AsyncMock()
            client.skills.list = AsyncMock(return_value=[])
            gc.return_value = client

            await h.handle(cmd, send)

        assert "No skills found" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_skill(self, cmdop_api_key):
        """show subcommand displays skill detail."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills show code-review")
        send = AsyncMock()

        detail = _make_skill_detail(name="code-review", content="System prompt here")

        with patch.object(h, "_get_client") as gc:
            client = AsyncMock()
            client.skills.show = AsyncMock(return_value=detail)
            gc.return_value = client

            await h.handle(cmd, send)

        text = send.call_args[0][0]
        assert "code-review" in text
        assert "System prompt here" in text

    @pytest.mark.asyncio
    async def test_show_not_found(self, cmdop_api_key):
        """show subcommand for missing skill shows error."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills show nonexistent")
        send = AsyncMock()

        detail = _make_skill_detail(found=False, name="nonexistent")

        with patch.object(h, "_get_client") as gc:
            client = AsyncMock()
            client.skills.show = AsyncMock(return_value=detail)
            gc.return_value = client

            await h.handle(cmd, send)

        assert "not found" in send.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_run_skill_success(self, cmdop_api_key):
        """run subcommand executes skill and shows result."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills run code-review Check this PR")
        send = AsyncMock()

        result = _make_skill_result(text="Looks good!", duration_ms=2000)

        with patch.object(h, "_get_client") as gc:
            client = AsyncMock()
            client.skills.run = AsyncMock(return_value=result)
            gc.return_value = client

            with patch("cmdop.models.skills.SkillRunOptions"):
                await h.handle(cmd, send)

        text = send.call_args[0][0]
        assert "Looks good!" in text
        assert "2.0s" in text

    @pytest.mark.asyncio
    async def test_run_skill_failure(self, cmdop_api_key):
        """run subcommand shows error on failure."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills run broken Do something")
        send = AsyncMock()

        result = _make_skill_result(success=False, text="", error="Timeout exceeded")

        with patch.object(h, "_get_client") as gc:
            client = AsyncMock()
            client.skills.run = AsyncMock(return_value=result)
            gc.return_value = client

            with patch("cmdop.models.skills.SkillRunOptions"):
                await h.handle(cmd, send)

        assert "Timeout exceeded" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_unknown_subcommand(self, cmdop_api_key):
        """Unknown subcommand shows error."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills delete something")
        send = AsyncMock()

        await h.handle(cmd, send)

        assert "Unknown subcommand" in send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_truncates_long_content(self, cmdop_api_key):
        """show truncates system prompt content over 500 chars."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)
        cmd = Command.parse("/skills show verbose-skill")
        send = AsyncMock()

        long_content = "X" * 800
        detail = _make_skill_detail(name="verbose-skill", content=long_content)

        with patch.object(h, "_get_client") as gc:
            mock_client = AsyncMock()
            mock_client.skills.show = AsyncMock(return_value=detail)
            gc.return_value = mock_client

            await h.handle(cmd, send)

        text = send.call_args[0][0]
        assert "(truncated)" in text
        assert text.count("X") == 500

    @pytest.mark.asyncio
    async def test_close(self, cmdop_api_key):
        """close() cleans up client."""
        from cmdop_bot.handlers.skills import SkillsHandler

        h = SkillsHandler(cmdop_api_key=cmdop_api_key)

        with patch("cmdop.AsyncCMDOPClient") as cls:
            client = AsyncMock()
            cls.remote.return_value = client

            # Force client creation
            await h._get_client()
            assert h._client is not None

            await h.close()
            assert h._client is None
            client.close.assert_called_once()


# ---------------------------------------------------------------------------
# Command parsing for /skills and /skill
# ---------------------------------------------------------------------------

class TestSkillsCommandParsing:
    """Tests for /skills and /skill command parsing."""

    def test_parse_skills_list(self):
        cmd = Command.parse("/skills list")
        assert cmd is not None
        assert cmd.name == "skills"
        assert cmd.args == ["list"]

    def test_parse_skills_show(self):
        cmd = Command.parse("/skills show code-review")
        assert cmd is not None
        assert cmd.name == "skills"
        assert cmd.args == ["show", "code-review"]

    def test_parse_skills_run(self):
        cmd = Command.parse("/skills run code-review Review this PR please")
        assert cmd is not None
        assert cmd.name == "skills"
        assert cmd.args == ["run", "code-review", "Review", "this", "PR", "please"]
        assert cmd.args_text == "run code-review Review this PR please"

    def test_parse_skill_shorthand(self):
        cmd = Command.parse("/skill code-review Review this")
        assert cmd is not None
        assert cmd.name == "skill"
        assert cmd.args[0] == "code-review"
        assert " ".join(cmd.args[1:]) == "Review this"


# ---------------------------------------------------------------------------
# Slack BlockBuilder — skills blocks
# ---------------------------------------------------------------------------

class TestSlackSkillsBlocks:
    """Tests for Slack Block Kit skills builders."""

    def test_skills_list_blocks(self):
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        skills = [_make_skill_info("ssl-check", "Check SSL", "builtin")]
        blocks = BlockBuilder.skills_list(skills)

        assert len(blocks) >= 2  # header + content
        assert blocks[0]["type"] == "header"
        assert "ssl-check" in blocks[1]["text"]["text"]

    def test_skills_list_empty(self):
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        blocks = BlockBuilder.skills_list([])

        assert len(blocks) == 2  # header + "no skills"
        assert "No skills found" in blocks[1]["text"]["text"]

    def test_skills_list_truncates_at_25(self):
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        skills = [_make_skill_info(f"skill-{i}", f"Desc {i}") for i in range(30)]
        blocks = BlockBuilder.skills_list(skills)

        # Should have footer context about truncation
        last = blocks[-1]
        assert last["type"] == "context"
        assert "30" in last["elements"][0]["text"]

    def test_skill_detail_found(self):
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        detail = _make_skill_detail()
        blocks = BlockBuilder.skill_detail(detail)

        assert blocks[0]["type"] == "header"
        assert "code-review" in blocks[0]["text"]["text"]

    def test_skill_detail_not_found(self):
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        detail = _make_skill_detail(found=False, name="missing")
        blocks = BlockBuilder.skill_detail(detail)

        # Should use error_message format
        assert "Not Found" in blocks[0]["text"]["text"]

    def test_skill_result_success(self):
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        result = _make_skill_result(text="All good", duration_ms=3000)
        blocks = BlockBuilder.skill_result("my-skill", "test prompt", result)

        assert blocks[0]["type"] == "header"
        assert "Result" in blocks[0]["text"]["text"]
        # Check duration in context
        duration_block = blocks[-1]
        assert duration_block["type"] == "context"
        assert "3.0s" in duration_block["elements"][0]["text"]

    def test_skill_result_error(self):
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        result = _make_skill_result(success=False, text="", error="Timed out")
        blocks = BlockBuilder.skill_result("my-skill", "test", result)

        assert "Error" in blocks[0]["text"]["text"]


# ---------------------------------------------------------------------------
# Discord EmbedBuilder — skills embeds
# ---------------------------------------------------------------------------

class TestDiscordSkillsEmbeds:
    """Tests for Discord embed builders for skills."""

    def test_skills_list_embed(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        skills = [
            _make_skill_info("ssl-check", "Check SSL", "builtin"),
            _make_skill_info("code-review", "Review code", "workspace"),
        ]
        embed = EmbedBuilder.skills_list(skills)

        assert embed.title == "Skills"
        assert "ssl-check" in embed.description
        assert "code-review" in embed.description

    def test_skills_list_empty_embed(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        embed = EmbedBuilder.skills_list([])

        assert "No skills found" in embed.description

    def test_skills_list_truncates_at_20(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        skills = [_make_skill_info(f"skill-{i}") for i in range(25)]
        embed = EmbedBuilder.skills_list(skills)

        assert embed.footer is not None
        assert "25" in embed.footer.text

    def test_skill_detail_embed(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        detail = _make_skill_detail()
        embed = EmbedBuilder.skill_detail(detail)

        assert "code-review" in embed.title
        field_names = [f.name for f in embed.fields]
        assert "Author" in field_names
        assert "Origin" in field_names

    def test_skill_detail_not_found_embed(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        detail = _make_skill_detail(found=False, name="missing")
        embed = EmbedBuilder.skill_detail(detail)

        assert embed.color.value == EmbedBuilder.COLOR_ERROR

    def test_skill_result_success_embed(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        result = _make_skill_result(text="All clear", duration_ms=1500)
        embed = EmbedBuilder.skill_result("my-skill", "check things", result)

        assert embed.color.value == EmbedBuilder.COLOR_SUCCESS
        assert embed.footer is not None
        assert "1.5s" in embed.footer.text
        # Check fields
        field_names = [f.name for f in embed.fields]
        assert "Skill" in field_names
        assert "Result" in field_names

    def test_skill_result_error_embed(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        result = _make_skill_result(success=False, text="", error="Boom")
        embed = EmbedBuilder.skill_result("my-skill", "do it", result)

        assert embed.color.value == EmbedBuilder.COLOR_ERROR

    def test_skill_result_truncates_long_text(self):
        discord = pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        result = _make_skill_result(text="X" * 2000)
        embed = EmbedBuilder.skill_result("s", "p", result)

        result_field = next(f for f in embed.fields if f.name == "Result")
        assert len(result_field.value) <= 1820  # 1800 + "... (truncated)"


# ---------------------------------------------------------------------------
# Telegram SkillsHandler
# ---------------------------------------------------------------------------

class TestTelegramSkillsHandler:
    """Tests for Telegram-specific SkillsHandler."""

    @pytest.fixture
    def tg_handler(self, mock_cmdop_handler):
        from cmdop_bot.channels.telegram.handlers.skills import SkillsHandler
        from cmdop_bot.channels.telegram.formatter import TelegramFormatter

        bot = AsyncMock()
        return SkillsHandler(
            bot=bot,
            cmdop=mock_cmdop_handler,
            formatter=TelegramFormatter(),
            allowed_users={123},
        )

    def _make_msg(self, text, user_id=123):
        """Create a mock aiogram Message."""
        msg = AsyncMock()
        msg.text = text
        msg.from_user = MagicMock()
        msg.from_user.id = user_id
        msg.chat = MagicMock()
        msg.chat.id = 999
        msg.answer = AsyncMock()
        return msg

    @pytest.mark.asyncio
    async def test_unauthorized_user(self, tg_handler):
        msg = self._make_msg("/skills list", user_id=999)
        await tg_handler.handle(msg)
        msg.answer.assert_called_once()
        assert "not authorized" in msg.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_no_args_shows_usage(self, tg_handler):
        msg = self._make_msg("/skills")
        await tg_handler.handle(msg)
        msg.answer.assert_called_once()
        text = msg.answer.call_args[0][0]
        assert "/skills list" in text

    @pytest.mark.asyncio
    async def test_list_skills(self, tg_handler, mock_cmdop_handler):
        msg = self._make_msg("/skills list")
        await tg_handler.handle(msg)

        mock_cmdop_handler.list_skills.assert_called_once()
        text = msg.answer.call_args[0][0]
        # MarkdownV2 escapes hyphens: code-review -> code\-review
        assert "code" in text and "review" in text

    @pytest.mark.asyncio
    async def test_list_empty(self, tg_handler, mock_cmdop_handler):
        mock_cmdop_handler.list_skills.return_value = []
        msg = self._make_msg("/skills list")
        await tg_handler.handle(msg)

        text = msg.answer.call_args[0][0]
        assert "No skills found" in text

    @pytest.mark.asyncio
    async def test_show_skill(self, tg_handler, mock_cmdop_handler):
        msg = self._make_msg("/skills show code-review")
        await tg_handler.handle(msg)

        mock_cmdop_handler.show_skill.assert_called_once_with("code-review")
        text = msg.answer.call_args[0][0]
        # MarkdownV2 escapes hyphens: code-review -> code\-review
        assert "code" in text and "review" in text

    @pytest.mark.asyncio
    async def test_show_not_found(self, tg_handler, mock_cmdop_handler):
        mock_cmdop_handler.show_skill.return_value = _make_skill_detail(found=False, name="nope")
        msg = self._make_msg("/skills show nope")
        await tg_handler.handle(msg)

        text = msg.answer.call_args[0][0]
        assert "not found" in text.lower()

    @pytest.mark.asyncio
    async def test_run_skill(self, tg_handler, mock_cmdop_handler):
        msg = self._make_msg("/skills run code-review Check this")
        await tg_handler.handle(msg)

        mock_cmdop_handler.run_skill.assert_called_once_with("code-review", "Check this")
        text = msg.answer.call_args[0][0]
        assert "Review complete" in text

    @pytest.mark.asyncio
    async def test_run_skill_error(self, tg_handler, mock_cmdop_handler):
        mock_cmdop_handler.run_skill.return_value = _make_skill_result(
            success=False, text="", error="Skill timed out"
        )
        msg = self._make_msg("/skills run slow-skill Do stuff")
        await tg_handler.handle(msg)

        text = msg.answer.call_args[0][0]
        assert "Skill timed out" in text

    @pytest.mark.asyncio
    async def test_skill_shorthand(self, tg_handler, mock_cmdop_handler):
        """The /skill command is a shorthand for /skills run."""
        msg = self._make_msg("/skill code-review Review this PR")
        await tg_handler.handle(msg)

        mock_cmdop_handler.run_skill.assert_called_once_with("code-review", "Review this PR")

    @pytest.mark.asyncio
    async def test_skill_shorthand_no_prompt(self, tg_handler):
        """The /skill command without a prompt shows usage."""
        msg = self._make_msg("/skill code-review")
        await tg_handler.handle(msg)

        text = msg.answer.call_args[0][0]
        assert "/skill" in text

    @pytest.mark.asyncio
    async def test_run_exception(self, tg_handler, mock_cmdop_handler):
        """Exception in run_skill is caught and sent as error."""
        mock_cmdop_handler.run_skill.side_effect = RuntimeError("connection lost")
        msg = self._make_msg("/skills run broken test")
        await tg_handler.handle(msg)

        msg.answer.assert_called()
        # Should have called send_error → formatter.error
        text = msg.answer.call_args[0][0]
        assert "Error" in text or "error" in text.lower()

    @pytest.mark.asyncio
    async def test_list_exception(self, tg_handler, mock_cmdop_handler):
        """Exception in list_skills is caught and sent as error."""
        mock_cmdop_handler.list_skills.side_effect = RuntimeError("no connection")
        msg = self._make_msg("/skills list")
        await tg_handler.handle(msg)

        msg.answer.assert_called()


# ---------------------------------------------------------------------------
# Integration: handler in mock_cmdop_handler fixture
# ---------------------------------------------------------------------------

class TestMockCMDOPHandlerSkillsFixture:
    """Verify mock_cmdop_handler fixture in test_handlers.py is extensible."""

    def test_mock_has_skills_methods(self, mock_cmdop_handler):
        """mock_cmdop_handler should have all three skills methods."""
        assert hasattr(mock_cmdop_handler, "list_skills")
        assert hasattr(mock_cmdop_handler, "show_skill")
        assert hasattr(mock_cmdop_handler, "run_skill")


# ---------------------------------------------------------------------------
# Help text includes skills
# ---------------------------------------------------------------------------

class TestHelpTextIncludesSkills:
    """Verify help text was updated to mention skills."""

    def test_telegram_start_mentions_skills(self):
        """StartHandler welcome text includes /skills."""
        import inspect
        from cmdop_bot.channels.telegram.handlers.commands import StartHandler

        source = inspect.getsource(StartHandler.handle)
        assert "/skills" in source

    def test_telegram_help_mentions_skills(self):
        """HelpHandler help text includes skills section."""
        import inspect
        from cmdop_bot.channels.telegram.handlers.commands import HelpHandler

        source = inspect.getsource(HelpHandler.handle)
        assert "Skills" in source
        assert "/skill" in source

    def test_slack_help_mentions_skills(self):
        """Slack help_message includes skills commands."""
        from cmdop_bot.channels.slack.blocks import BlockBuilder

        blocks = BlockBuilder.help_message()
        text = str(blocks)
        assert "skills" in text

    def test_discord_help_mentions_skills(self):
        """Discord help_embed includes skills commands."""
        pytest.importorskip("discord")
        from cmdop_bot.channels.discord.embeds import EmbedBuilder

        embed = EmbedBuilder.help_embed()
        field_names = [f.name for f in embed.fields]
        assert any("skills" in n.lower() for n in field_names)
