#!/usr/bin/env python3
"""Using CMDOPHandler directly in your own bot.

CMDOPHandler contains all CMDOP logic - use it to build custom integrations.

Prerequisites:
    1. Get CMDOP API key from https://my.cmdop.com/dashboard/settings/
    2. pip install cmdop-bot

Usage:
    python handler_example.py
"""

import asyncio
from cmdop_bot import CMDOPHandler, Model


async def main():
    async with CMDOPHandler(
        api_key="cmdop_xxx",  # https://my.cmdop.com/dashboard/settings/
        machine="my-server",
        model=Model.balanced(),
    ) as cmdop:
        # Run AI agent
        result = await cmdop.run_agent("What's the disk usage?")
        print(result.text)

        # Execute shell command
        output, code = await cmdop.execute_shell("ls -la")
        print(output.decode())

        # List files
        files = await cmdop.list_files("/var/log")
        for f in files.entries:
            print(f.name)

        # Switch machine
        await cmdop.set_machine("other-server")


if __name__ == "__main__":
    asyncio.run(main())
