# Discord Bot Implementation Patterns

## Official Documentation Reference

**Source:** https://discordpy.readthedocs.io/en/stable/

This document outlines the correct patterns for Discord bot initialization and management based on the official discord.py documentation.

## Bot Initialization Pattern

### Correct Pattern (From Official Docs)

**Two approaches are supported:**

**Approach 1: Client Subclassing**
```python
import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
    
    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('my token goes here')
```

**Approach 2: Event Decorator**
```python
import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged on as {client.user}!')

@client.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')

client.run('my token goes here')
```

### Key Requirements

**1. Intents Are Required:**
```python
# ❌ WRONG - will fail with TypeError
client = discord.Client()

# ✅ CORRECT - intents parameter is required
intents = discord.Intents.default()
client = discord.Client(intents=intents)
```

**2. Privileged Intents Must Be Enabled:**

For our MCP Discord server, we need:
```python
intents = discord.Intents.default()
intents.message_content = True  # Required for message content
intents.members = True          # Required for member data
intents.presences = True        # Required for presence updates (optional)
```

**These must be enabled in Discord Developer Portal:**
1. Go to https://discord.com/developers/applications/
2. Select your application
3. Go to "Bot" section
4. Enable "Privileged Gateway Intents":
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
   - PRESENCE INTENT (if needed)

### Our Implementation

**Location:** `run.py` and `TEMP/run_discord_tests.py`

**Pattern:**
```python
import discord
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get token
token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("No Discord bot token found")

# Create intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True  # Required for guild events

# Create client
bot = discord.Client(intents=intents)

# Register event handlers
@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name} (ID: {bot.user.id})')
    
    # Initialize MCP CE runtime with bot
    from mcp_ce.tools.discord._bot_helper import set_bot
    set_bot(bot)
    
    # Run your logic here
    # ...

# Start bot
bot.run(token)
```

## Common Mistakes

### Mistake 1: Missing Intents

**Problem:**
```python
# ❌ WRONG - TypeError: __init__() missing 1 required keyword-only argument: 'intents'
bot = discord.Client()
```

**Solution:**
```python
# ✅ CORRECT
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
```

### Mistake 2: Privileged Intents Not Enabled

**Problem:**
```
discord.errors.PrivilegedIntentsRequired: Shard ID None is requesting privileged intents that have not been explicitly enabled in the developer portal.
```

**Solution:**
1. Enable intents in Discord Developer Portal (see above)
2. Wait a few minutes for changes to propagate
3. Restart your bot

### Mistake 3: Using Wrong Token Variable

**Problem:**
```python
# ❌ WRONG - may use wrong environment variable
token = os.getenv("DISCORD_TOKEN")
```

**Our Solution:**
```python
# ✅ CORRECT - handles both DISCORD_TOKEN and DISCORD_BOT_TOKEN
token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")
```

### Mistake 4: Not Awaiting Bot Connection

**Problem:**
```python
# ❌ WRONG - bot not connected when tools are called
bot = discord.Client(intents=intents)
set_bot(bot)  # Bot not connected yet!
await run_tests()
```

**Solution:**
```python
# ✅ CORRECT - wait for on_ready event
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    set_bot(bot)  # Bot is now connected
    await run_tests()

bot.run(token)
```

## Bot Helper Pattern

**Location:** `src/mcp_ce/tools/discord/_bot_helper.py`

**Purpose:** Singleton pattern for bot instance access across tools

**Implementation:**
```python
from typing import Optional
import discord

_bot_instance: Optional[discord.Client] = None

def set_bot(bot: discord.Client) -> None:
    """
    Set the Discord bot instance (singleton pattern).
    
    This should be called once during server initialization,
    after the bot is connected and ready.
    
    Args:
        bot: The Discord bot instance
    """
    global _bot_instance
    _bot_instance = bot

def get_bot() -> discord.Client:
    """
    Get the Discord bot instance (singleton pattern).
    
    Returns:
        The Discord bot instance
        
    Raises:
        RuntimeError: If bot not initialized (call set_bot() first)
    """
    if _bot_instance is None:
        raise RuntimeError(
            "Discord bot not initialized. "
            "Call set_bot(bot) after bot.on_ready() event."
        )
    return _bot_instance

def is_bot_ready() -> bool:
    """Check if bot is initialized and ready."""
    return _bot_instance is not None and _bot_instance.is_ready()
```

## Event Handling

**Key Events:**

```python
@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord."""
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    """Called when a message is received."""
    if message.author == bot.user:
        return  # Ignore bot's own messages
    print(f'Message from {message.author}: {message.content}')

@bot.event
async def on_error(event, *args, **kwargs):
    """Called when an error occurs in an event handler."""
    import traceback
    traceback.print_exc()
```

## Integration with MCP CE

**Pattern:**
```python
# In run.py or test runner
from mcp_ce.tools.discord._bot_helper import set_bot

@bot.event
async def on_ready():
    print(f'Bot connected: {bot.user.name}')
    
    # Initialize MCP CE runtime with bot instance
    set_bot(bot)
    
    # Now tools can access bot via get_bot()
    # ... run your application logic
```

**In Tools:**
```python
from ._bot_helper import get_bot

async def send_message(channel_id: str, content: str):
    bot = get_bot()  # Retrieves singleton instance
    channel = bot.get_channel(int(channel_id))
    # ... tool implementation
```

## Testing Patterns

**Live Server Testing:**
```python
import asyncio
import discord
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = discord.Client(intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'Bot ready: {bot.user.name}')
        
        # Set bot instance for tools
        from mcp_ce.tools.discord._bot_helper import set_bot
        set_bot(bot)
        
        # Run tests
        from TESTS.mcp_ce.tools.discord.test_discord_tools import test_discord_tools
        try:
            await test_discord_tools()
            print("✅ All tests passed!")
        except Exception as e:
            print(f"❌ Tests failed: {e}")
        finally:
            await bot.close()
    
    # Start bot
    token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
```

## Cache-Related Issues

**Problem:** Old cached data with dict format causes runtime failures even after code refactoring.

**Symptoms:**
- Tool compiles successfully
- Runtime error: `TypeError: Tool 'discord.tool_name' must return ToolResponse, got dict`
- Occurs on cache hit (cached data from before refactoring)

**Solution:**
```powershell
# Clear all caches after major refactoring
Remove-Item -Path ".cache\*" -Recurse -Force
```

**See Also:** `docs/CACHE_MIGRATION_GUIDE.md` for detailed cache management.

## Resources

- **Official Documentation:** https://discordpy.readthedocs.io/en/stable/
- **API Reference:** https://discordpy.readthedocs.io/en/stable/api.html
- **Discord Developer Portal:** https://discord.com/developers/applications/
- **MCP Discord Repository:** Internal documentation in `.github/copilot-instructions.md`
