"""Discord bot implementation using discord.py."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cmdop_bot.core.base import BaseChannel
from cmdop_bot.core.permissions import PermissionManager
from cmdop_bot.channels.discord.embeds import EmbedBuilder

if TYPE_CHECKING:
    import discord
    from discord import app_commands
    from cmdop import AsyncCMDOPClient

logger = logging.getLogger(__name__)


class DiscordBot(BaseChannel):
    """Discord bot using discord.py with CMDOP SDK integration.

    Uses slash commands for all operations.

    Example:
        >>> bot = DiscordBot(
        ...     token="DISCORD_BOT_TOKEN",
        ...     cmdop_api_key="cmd_xxx",
        ...     guild_ids=[123456789],  # Optional: specific guilds
        ... )
        >>> bot.run()
    """

    def __init__(
        self,
        token: str,
        cmdop_api_key: str,
        *,
        guild_ids: list[int] | None = None,
        allowed_users: list[int] | None = None,
        permissions: PermissionManager | None = None,
        machine: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Discord bot.

        Args:
            token: Discord bot token
            cmdop_api_key: CMDOP API key (cmd_xxx format)
            guild_ids: List of guild IDs for slash commands. None = global.
            allowed_users: List of allowed Discord user IDs. None = allow all.
            permissions: Permission manager for fine-grained control
            machine: Target machine hostname. None = use default machine.
            timeout: Default command timeout in seconds.
        """
        super().__init__(token, cmdop_api_key)
        self._guild_ids = guild_ids
        self._allowed_users = set(allowed_users) if allowed_users else None
        self._permissions = permissions or PermissionManager()
        self._machine = machine
        self._timeout = timeout

        self._bot: discord.Client | None = None
        self._tree: app_commands.CommandTree | None = None
        self._cmdop_client: AsyncCMDOPClient | None = None

    @property
    def name(self) -> str:
        return "discord"

    async def _get_cmdop_client(self) -> AsyncCMDOPClient:
        """Get or create CMDOP client (lazy initialization)."""
        if self._cmdop_client is None:
            from cmdop import AsyncCMDOPClient

            self._cmdop_client = AsyncCMDOPClient.remote(api_key=self._cmdop_api_key)

            if self._machine:
                await self._cmdop_client.terminal.set_machine(self._machine)
                logger.info(f"Connected to machine: {self._machine}")

        return self._cmdop_client

    def _is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        if self._allowed_users is None:
            return True
        return user_id in self._allowed_users

    async def start(self) -> None:
        """Start the bot."""
        try:
            import discord
            from discord import app_commands
        except ImportError as e:
            raise ImportError(
                "discord.py is required for Discord. Install with: pip install cmdop-sdk[discord]"
            ) from e

        # Create bot with minimal intents
        intents = discord.Intents.default()
        self._bot = discord.Client(intents=intents)
        self._tree = app_commands.CommandTree(self._bot)
        self._running = True

        # Register commands
        self._register_commands()

        @self._bot.event
        async def on_ready():
            logger.info(f"Discord bot logged in as {self._bot.user}")
            # Sync commands
            if self._guild_ids:
                for guild_id in self._guild_ids:
                    guild = discord.Object(id=guild_id)
                    self._tree.copy_global_to(guild=guild)
                    await self._tree.sync(guild=guild)
                    logger.info(f"Synced commands to guild {guild_id}")
            else:
                await self._tree.sync()
                logger.info("Synced global commands")

        logger.info("Starting Discord bot...")
        await self._bot.start(self._token)

    def _register_commands(self) -> None:
        """Register slash commands."""
        import discord
        from discord import app_commands

        @self._tree.command(name="help", description="Show available commands")
        async def cmd_help(interaction: discord.Interaction):
            if not self._is_allowed(interaction.user.id):
                await interaction.response.send_message(
                    "You are not authorized to use this bot.",
                    ephemeral=True,
                )
                return

            embed = EmbedBuilder.help_embed()
            await interaction.response.send_message(embed=embed)

        @self._tree.command(name="shell", description="Execute shell command")
        @app_commands.describe(command="Shell command to execute")
        async def cmd_shell(interaction: discord.Interaction, command: str):
            await self._handle_shell(interaction, command)

        @self._tree.command(name="exec", description="Execute shell command (alias)")
        @app_commands.describe(command="Shell command to execute")
        async def cmd_exec(interaction: discord.Interaction, command: str):
            await self._handle_shell(interaction, command)

        @self._tree.command(name="agent", description="Run AI agent task")
        @app_commands.describe(task="Task description for the AI agent")
        async def cmd_agent(interaction: discord.Interaction, task: str):
            await self._handle_agent(interaction, task)

        @self._tree.command(name="machine", description="Set target machine")
        @app_commands.describe(hostname="Machine hostname")
        async def cmd_machine(interaction: discord.Interaction, hostname: str):
            await self._handle_machine(interaction, hostname)

        @self._tree.command(name="status", description="Show connection status")
        async def cmd_status(interaction: discord.Interaction):
            await self._handle_status(interaction)

        @self._tree.command(name="ls", description="List directory contents")
        @app_commands.describe(path="Directory path to list (default: current)")
        async def cmd_ls(interaction: discord.Interaction, path: str = "."):
            await self._handle_ls(interaction, path)

        @self._tree.command(name="cat", description="Read file contents")
        @app_commands.describe(path="File path to read")
        async def cmd_cat(interaction: discord.Interaction, path: str):
            await self._handle_cat(interaction, path)

    async def _handle_shell(
        self,
        interaction: discord.Interaction,
        command: str,
    ) -> None:
        """Handle /shell command."""
        import discord

        if not self._is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are not authorized to use this bot.",
                ephemeral=True,
            )
            return

        # Defer response (command may take time)
        await interaction.response.defer()

        try:
            client = await self._get_cmdop_client()

            output, exit_code = await client.terminal.execute(
                command,
                timeout=self._timeout,
            )

            # Decode output
            output_text = output.decode("utf-8", errors="replace")

            # Create embed
            embed = EmbedBuilder.code_output(
                command=command,
                output=output_text,
                exit_code=exit_code,
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.exception("Shell command failed")
            embed = EmbedBuilder.error("Command Failed", str(e))
            await interaction.followup.send(embed=embed)

    async def _handle_agent(
        self,
        interaction: discord.Interaction,
        task: str,
    ) -> None:
        """Handle /agent command."""
        import discord

        if not self._is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are not authorized to use this bot.",
                ephemeral=True,
            )
            return

        # Defer response (agent may take time)
        await interaction.response.defer()

        try:
            client = await self._get_cmdop_client()

            result = await client.agent.run(task)

            embed = EmbedBuilder.agent_result(
                task=task,
                result=result.text or "Task completed.",
                success=result.success,
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.exception("Agent task failed")
            embed = EmbedBuilder.error("Agent Failed", str(e))
            await interaction.followup.send(embed=embed)

    async def _handle_machine(
        self,
        interaction: discord.Interaction,
        hostname: str,
    ) -> None:
        """Handle /machine command."""
        import discord

        if not self._is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are not authorized to use this bot.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            client = await self._get_cmdop_client()
            session = await client.terminal.set_machine(hostname)

            embed = EmbedBuilder.machine_info(
                hostname=session.machine_hostname,
                os=session.os,
                shell=session.shell,
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.exception("Machine selection failed")
            embed = EmbedBuilder.error("Connection Failed", str(e))
            await interaction.followup.send(embed=embed)

    async def _handle_status(self, interaction: discord.Interaction) -> None:
        """Handle /status command."""
        import discord

        if not self._is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are not authorized to use this bot.",
                ephemeral=True,
            )
            return

        try:
            client = await self._get_cmdop_client()

            embed = discord.Embed(
                title="🔌 Connection Status",
                color=EmbedBuilder.COLOR_CMDOP,
            )

            embed.add_field(
                name="Mode",
                value=client.mode,
                inline=True,
            )
            embed.add_field(
                name="Connected",
                value="✅ Yes" if client.is_connected else "❌ No",
                inline=True,
            )

            current_session = client.terminal.current_session
            if current_session:
                embed.add_field(
                    name="Current Machine",
                    value=f"`{current_session.machine_hostname}`",
                    inline=False,
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            embed = EmbedBuilder.error("Status Error", str(e))
            await interaction.response.send_message(embed=embed)

    async def _handle_ls(
        self,
        interaction: discord.Interaction,
        path: str,
    ) -> None:
        """Handle /ls command."""
        import discord

        if not self._is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are not authorized to use this bot.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            client = await self._get_cmdop_client()
            response = await client.files.list(path)
            entries = response.entries

            embed = EmbedBuilder.file_list(path, entries)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.exception("List directory failed")
            embed = EmbedBuilder.error("List Failed", str(e))
            await interaction.followup.send(embed=embed)

    async def _handle_cat(
        self,
        interaction: discord.Interaction,
        path: str,
    ) -> None:
        """Handle /cat command."""
        import discord

        if not self._is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are not authorized to use this bot.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            client = await self._get_cmdop_client()
            content = await client.files.read(path)

            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    embed = discord.Embed(
                        title="📄 Binary File",
                        description=f"`{path}`\nSize: {len(content)} bytes",
                        color=EmbedBuilder.COLOR_CMDOP,
                    )
                    await interaction.followup.send(embed=embed)
                    return

            embed = EmbedBuilder.file_content(path, content)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.exception("Read file failed")
            embed = EmbedBuilder.error("Read Failed", str(e))
            await interaction.followup.send(embed=embed)

    async def stop(self) -> None:
        """Stop the bot."""
        self._running = False
        if self._bot:
            await self._bot.close()
        if self._cmdop_client:
            await self._cmdop_client.close()
            self._cmdop_client = None
        logger.info("Discord bot stopped")

    async def send(self, chat_id: str, text: str) -> None:
        """Send message to channel."""
        if self._bot:
            channel = self._bot.get_channel(int(chat_id))
            if channel:
                await channel.send(text)
