# MCP Discord Server Setup Guide

This folder contains setup instructions and scripts for deploying a fresh MCP Discord server.

## Quick Start

### Prerequisites

- Python 3.10+ (3.13+ recommended)
- [uv](https://github.com/astral-sh/uv) package manager
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hanweg/mcp-discord.git
   cd mcp-discord
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   # Copy the example .env file (if it exists) or create one
   cp .env.example .env  # or create .env manually
   ```

4. **Add your Discord token to `.env`:**
   ```env
   DISCORD_TOKEN=your_bot_token_here
   ```

5. **Verify installation:**
   ```bash
   uv run mcp-discord --info
   ```

## Entry Points

### `mcp-discord` (Recommended)

Main entry point that initializes the Discord bot and runs the MCP server:

```bash
uv run mcp-discord
```

**Configuration for MCP clients:**

**Claude Desktop** (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):
```json
{
  "mcpServers": {
    "mcp-discord": {
      "command": "uv",
      "args": [
        "--directory",
        "D:\\GitHub\\mcp-discord",
        "run",
        "mcp-discord"
      ],
      "env": {
        "DISCORD_TOKEN": "your_bot_token_here"
      }
    }
  }
}
```

**Cursor** (automated setup available):

**Option 1: Automated Setup (Recommended)**
```bash
# Windows PowerShell
.\setup\configure-cursor.ps1

# macOS/Linux
chmod +x setup/configure-cursor.sh
./setup/configure-cursor.sh
```

**Option 2: Manual Setup**

1. Open Cursor Settings (`Ctrl+Shift+J` or `Cmd+Shift+J`)
2. Navigate to MCP settings
3. Copy the configuration from `setup/cursor-mcp-config.json`
4. Update paths and API keys as needed

The config includes:
- **mcp-discord**: Your Discord MCP server
- **linear**: Linear issue tracking integration
- **context7**: Context7 documentation and code examples

See `setup/cursor-mcp-config.json` for the full configuration.

### `mcp-code-execution`

Alternative entry point that runs the MCP server without Discord bot initialization (Discord tools won't work):

```bash
uv run mcp-code-execution
```

## Discord Bot Setup

1. **Create a Discord Application:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Give it a name and create it

2. **Create a Bot:**
   - Go to the "Bot" section
   - Click "Add Bot"
   - Copy the bot token (you'll need this for `DISCORD_TOKEN`)

3. **Enable Required Intents:**
   - In the Bot section, enable:
     - **MESSAGE CONTENT INTENT** (required for reading messages)
     - **PRESENCE INTENT** (optional, for presence features)
     - **SERVER MEMBERS INTENT** (required for member operations)

4. **Invite Bot to Server:**
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select bot permissions:
     - Read Messages/View Channels
     - Send Messages
     - Manage Messages
     - Manage Events
     - Manage Roles
     - Manage Channels
   - Copy the generated URL and open it in a browser
   - Select your server and authorize

## Troubleshooting

### Server Won't Start

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Verify dependencies:**
   ```bash
   uv sync
   ```

3. **Check Discord token:**
   - Ensure `DISCORD_TOKEN` is set in `.env` or environment
   - Verify the token is valid in Discord Developer Portal

4. **Check logs:**
   - The server logs to stdout/stderr
   - Look for error messages about missing modules or authentication failures

### Discord Tools Not Working

- Ensure the Discord bot is properly initialized (check logs for "Discord bot logged in")
- Verify bot has necessary permissions in your Discord server
- Check that required intents are enabled in Discord Developer Portal

### Import Errors

- Make sure you're running from the project root
- Try reinstalling: `uv sync --reinstall`
- Check that `src/discord_mcp` and `src/mcp_ce` are in your Python path

## Development

### Running Tests

```bash
uv run pytest
# or
uv run python run_tests.py
```

### Adding New Tools

1. Add tool implementation to `src/mcp_ce/tools/<category>/`
2. Register tool in `src/mcp_ce/runtime.py` (`_SERVERS_REGISTRY`)
3. Add tool documentation in `query_tool_docs()` function
4. Add tool execution in `_execute_tool()` function

### Hot Reloading

MCP servers don't support hot reloading. To test changes:
1. Stop the server (Ctrl+C)
2. Make your changes
3. Restart the server
4. MCP clients will reconnect automatically

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)

