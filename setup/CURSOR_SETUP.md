# Cursor MCP Server Configuration

This guide helps you configure Cursor IDE to use your MCP Discord server along with Linear and Context7 MCP servers.

## Quick Setup

### Automated Configuration (Recommended)

**Windows:**
```powershell
.\setup\configure-cursor.ps1
```

**macOS/Linux:**
```bash
chmod +x setup/configure-cursor.sh
./setup/configure-cursor.sh
```

The script will:
1. Create the Cursor MCP config directory if needed
2. Back up any existing config
3. Prompt you for API keys/tokens
4. Create the configuration file

### Manual Configuration

1. **Locate Cursor Config Directory:**
   - **Windows**: `%APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\settings\`
   - **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/`
   - **Linux**: `~/.config/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/`

2. **Create or Edit Config File:**
   - File name: `cline_mcp_settings.json`
   - Copy the template from `setup/cursor-mcp-config.json`
   - Update paths and API keys

3. **Restart Cursor** to load the new MCP servers

## MCP Servers Included

### 1. mcp-discord

Your Discord MCP server with Discord bot integration.

**Required:**
- `DISCORD_TOKEN`: Your Discord bot token

**Features:**
- Server and channel management
- Message operations
- Role management
- Scheduled event creation/editing

### 2. linear

Linear issue tracking and project management.

**Required:**
- `LINEAR_API_KEY`: Your Linear API key

**Getting a Linear API Key:**
1. Go to [Linear Settings](https://linear.app/settings/api)
2. Create a new API key
3. Copy the key

**Features:**
- View and create Linear issues
- Link issues to code
- Project management

### 3. context7

Context7 provides up-to-date code documentation and examples.

**Required:**
- `CONTEXT7_API_KEY`: Your Context7 API key

**Getting a Context7 API Key:**
1. Sign up at [Context7](https://context7.com)
2. Get your API key from the dashboard
3. Copy the key

**Features:**
- Access to library documentation
- Code examples and snippets
- Up-to-date API references

## Using MCP Servers in Cursor

Once configured, you can use MCP servers in several ways:

### 1. Inline Agent

The Cursor inline agent can automatically use MCP servers when relevant:
- Ask about Linear issues: "What's the status of issue XYZ?"
- Get documentation: "Show me how to use FastMCP"
- Discord operations: "List channels in my Discord server"

### 2. Chat Interface

In Cursor's chat, you can explicitly reference MCP servers:
- "Use Linear to create an issue for this bug"
- "Get Context7 docs for discord.py"
- "Check Discord server info"

### 3. Memories

Cursor can use MCP servers to enhance memories:
- Store context from Linear issues
- Reference documentation from Context7
- Track Discord server configurations

## Troubleshooting

### MCP Server Not Connecting

1. **Check Config File:**
   - Verify `cline_mcp_settings.json` exists
   - Check JSON syntax is valid
   - Ensure paths are correct (use absolute paths)

2. **Check API Keys:**
   - Verify tokens/keys are correct
   - Check for typos or extra spaces
   - Ensure keys have proper permissions

3. **Check Logs:**
   - Open Cursor Developer Tools (`Help` → `Toggle Developer Tools`)
   - Look for MCP-related errors in console

4. **Verify Dependencies:**
   - For `mcp-discord`: Ensure `uv` is installed and in PATH
   - For `linear`: Ensure `npx` is available (comes with Node.js)
   - For `context7`: Ensure `npx` is available

### Server Timeout

If MCP servers timeout:
- Check that the server process can start
- Verify network connectivity (for remote servers)
- Increase timeout in Cursor settings if available

### Permission Errors

- Ensure Cursor has permission to execute the commands
- Check file permissions on config directory
- Verify API keys have correct scopes/permissions

## Updating Configuration

To update your MCP server configuration:

1. Edit `cline_mcp_settings.json` directly
2. Or run the configuration script again (it will back up the old config)
3. Restart Cursor

## Additional Resources

- [Cursor MCP Documentation](https://docs.cursor.com/context/mcp)
- [Linear MCP Server](https://linear.app/integrations/cursor-mcp)
- [Context7 Documentation](https://context7.com/docs)

