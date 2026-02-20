"""Direct test for handlers without Telegram."""
import asyncio
import os

async def test_files_handler():
    """Test FilesHandler directly."""
    from cmdop_bot.handlers.files import FilesHandler
    from cmdop_bot.models import Command
    
    # Get API key from env
    api_key = os.environ.get("CMDOP_API_KEY", "cmdop_live_mVcCRPiG5xaHN51tCAWF0rEN")
    machine = "ip-172-31-56-249"
    
    handler = FilesHandler(cmdop_api_key=api_key, machine=machine)
    
    results = []
    async def send(msg: str):
        print(f"[BOT RESPONSE]: {msg}")
        results.append(msg)
    
    # Test /ls
    print("\n=== Testing /ls ===")
    cmd = Command(name="ls", args="", raw_text="/ls", user_id="test", chat_id="test")
    await handler.handle(cmd, send)
    
    # Test /ls /home
    print("\n=== Testing /ls /home ===")
    cmd = Command(name="ls", args="/home", raw_text="/ls /home", user_id="test", chat_id="test")
    await handler.handle(cmd, send)
    
    return results

async def test_cmdop_direct():
    """Test CMDOP SDK directly."""
    from cmdop import AsyncCMDOPClient
    
    api_key = os.environ.get("CMDOP_API_KEY", "cmdop_live_mVcCRPiG5xaHN51tCAWF0rEN")
    machine = "ip-172-31-56-249"
    
    print(f"\n=== Direct CMDOP test ===")
    print(f"API Key: {api_key[:20]}...")
    print(f"Machine: {machine}")
    
    async with AsyncCMDOPClient.remote(api_key=api_key) as client:
        print("\n1. Setting machine for files service...")
        session = await client.files.set_machine(machine)
        print(f"   Session: {session.session_id[:8]}... on {session.machine_hostname}")
        
        print("\n2. Listing root directory...")
        response = await client.files.list("/")
        print(f"   Found {len(response.entries)} entries:")
        for e in response.entries[:10]:
            print(f"     - {e.name} ({e.type.value})")
        
        print("\n3. Listing home directory...")
        response = await client.files.list("/home")
        print(f"   Found {len(response.entries)} entries:")
        for e in response.entries[:10]:
            print(f"     - {e.name} ({e.type.value})")

if __name__ == "__main__":
    print("=" * 60)
    print("CMDOP Bot Handler Test")
    print("=" * 60)
    
    # First test SDK directly
    asyncio.run(test_cmdop_direct())
    
    # Then test handler
    # asyncio.run(test_files_handler())
