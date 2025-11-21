# GitHub Copilot MCP Integration Guide

This guide explains how to use the MCP Discord server with GitHub Copilot in VS Code.

## Quick Setup (Automated)

Run the setup script to automatically configure VS Code:

```bash
# Setup for workspace (recommended)
python setup_copilot_mcp.py

# Or setup globally (for all workspaces)
python setup_copilot_mcp.py --global
```

The script will:
1. ✅ Verify prerequisites (uv, .env, project files)
2. ✅ Generate VS Code MCP configuration
3. ✅ Update settings.json with server details
4. ✅ Show next steps and available tools

## Manual Setup

If you prefer to configure manually:

### 1. Add to VS Code Settings

**File:** `.vscode/settings.json` (workspace) or User Settings (global)

```json
{
  "github.copilot.chat.mcp.servers": {
    "discord-mcp": {
      "command": "uv",
      "args": ["run", "python", "run.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

**Note:** Environment variables are loaded from `.env` automatically by `run.py`.

### 2. Reload VS Code

- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type: "Reload Window"
- Press Enter

### 3. Verify Setup

Open Copilot Chat (`Ctrl+Alt+I` or `Cmd+Alt+I`) and type:

```
@workspace list available tools
```

You should see 34 tools from the MCP Discord server.

## Available Tools (34 Total)

### Discord Tools (21)
- `send_message` - Send message to Discord channel
- `get_server_info` - Get server information
- `get_channels` - List all channels in a server
- `get_user_info` - Get user profile information
- `create_scheduled_event` - Create scheduled Discord event
- `edit_scheduled_event` - Modify existing event
- `create_text_channel` - Create new text channel
- `create_category` - Create channel category
- `delete_channel` - Delete a channel
- `add_reaction` - Add emoji reaction to message
- `add_multiple_reactions` - Add multiple reactions at once
- `add_role` - Assign role to user
- `remove_role` - Remove role from user
- `list_members` - List server members
- `list_servers` - List all servers bot is in
- `moderate_message` - Moderate message (delete/pin)
- `pin_message` - Pin message to channel
- `unpin_message` - Unpin message from channel
- `remove_reaction` - Remove reaction from message
- `send_dm` - Send direct message to user
- `send_file` - Send file attachment to channel

### YouTube Tools (3)
- `get_video_metadata` - Get video title, channel, duration, etc.
- `get_transcript` - Extract video transcript/captions
- `search_youtube` - Search for videos by query

### Notion Tools (6)
- `create_notion_page` - Create new Notion page
- `get_notion_page` - Retrieve page content
- `update_notion_page` - Update existing page
- `query_notion_database` - Query database with filters
- `search_notion` - Search across workspace
- `add_notion_comment` - Add comment to page

### Crawl4AI Tools (3)
- `crawl_website` - Scrape website content
- `deep_crawl` - Multi-level website crawling
- `save_article` - Extract and save article content

### URL Ping (1)
- `ping_url` - Check if URL is accessible

## Example Workflows

### Workflow 1: Discord Event Creation

```
@workspace Create a Discord scheduled event:
- Title: "Code Review Session"
- Date: November 20, 2025 at 2:00 PM
- Server ID: 123456789
- Channel ID: 987654321
- Description: "Weekly code review and discussion"
```

### Workflow 2: YouTube Research

```
@workspace 
1. Get the transcript for YouTube video abc123xyz
2. Summarize the key points
3. Create a Notion page with the summary
```

### Workflow 3: Website Documentation

```
@workspace 
1. Crawl https://example.com/docs
2. Extract all articles
3. Save to Notion database "Documentation"
4. Send summary to Discord channel 999888777
```

### Workflow 4: Server Management

```
@workspace 
1. Get info about Discord server 123456789
2. List all channels
3. Create a new text channel called "announcements"
4. Send a welcome message to the new channel
```

## Using Natural Language

Copilot understands natural language, so you can be conversational:

**Instead of:**
```
@workspace send_message(channel_id="123", content="Hello")
```

**Just say:**
```
@workspace Send "Hello" to Discord channel 123
```

**Instead of:**
```
@workspace get_video_metadata(video_id="abc123")
```

**Just say:**
```
@workspace What's the title of YouTube video abc123?
```

## Troubleshooting

### Tools Not Appearing

1. **Check MCP Server Logs:**
   - View → Output → Select "Model Context Protocol" from dropdown

2. **Verify Configuration:**
   ```bash
   # Test MCP runtime
   uv run python -c "from src.mcp_ce.runtime import discovered_servers; import json; print(json.dumps(discovered_servers(), indent=2))"
   ```

3. **Check Environment Variables:**
   ```bash
   # Verify .env file exists and has required tokens
   cat .env  # Linux/Mac
   type .env  # Windows
   ```

4. **Restart VS Code:**
   - Completely close and reopen VS Code
   - Or reload window: `Ctrl+Shift+P` → "Reload Window"

### Server Not Starting

1. **Check Python/uv Installation:**
   ```bash
   uv --version
   python --version
   ```

2. **Test Server Standalone:**
   ```bash
   uv run python run.py
   ```

3. **Check Dependencies:**
   ```bash
   uv sync
   ```

### Permission Errors

If you get permission errors, ensure:
- `.env` file has correct Discord bot token
- Bot has required Discord permissions (MESSAGE_CONTENT, PRESENCE, SERVER_MEMBERS intents)
- API keys are valid (YouTube, Notion, OpenAI)

## Configuration Options

### Minimal Configuration

Don't need environment variables in settings (run.py loads .env):

```json
{
  "github.copilot.chat.mcp.servers": {
    "discord-mcp": {
      "command": "uv",
      "args": ["run", "python", "run.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### With Explicit Environment Variables

If you want to override .env or use different credentials:

```json
{
  "github.copilot.chat.mcp.servers": {
    "discord-mcp": {
      "command": "uv",
      "args": ["run", "python", "run.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "DISCORD_TOKEN": "your-token-here",
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Using Python Directly (Without uv)

```json
{
  "github.copilot.chat.mcp.servers": {
    "discord-mcp": {
      "command": "python",
      "args": ["run.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

## Security Considerations

⚠️ **Important:** If you add tokens to VS Code settings, they are stored in plain text.

**Recommended Approach:**
- Keep tokens in `.env` file (already in `.gitignore`)
- Let `run.py` load `.env` automatically
- Don't include `env` key in MCP configuration

**Alternative (More Secure):**
- Use environment variables at OS level
- Or use a secrets manager
- Configure MCP to reference system environment

## Performance Tips

1. **Cache Behavior:**
   - Many tools use caching (YouTube metadata: 1hr, transcripts: 2hr)
   - Use `override_cache=True` parameter to force fresh data

2. **Rate Limiting:**
   - Discord API has rate limits (handle automatically)
   - YouTube API has daily quota
   - Notion API has rate limits

3. **Background Operations:**
   - Some tools run in background (deep_crawl)
   - Check logs for completion status

## Next Steps

1. ✅ Run setup script: `python setup_copilot_mcp.py`
2. ✅ Reload VS Code window
3. ✅ Open Copilot Chat and try: `@workspace list available tools`
4. ✅ Test a simple command: `@workspace Get server info for Discord server [your-server-id]`

## Support

- **Documentation:** See `.github/copilot-instructions.md` for development patterns
- **Issues:** Check `TESTS/` directory for tool examples
- **Logs:** View → Output → "Model Context Protocol"

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [GitHub Copilot MCP Support](https://code.visualstudio.com/docs/copilot/copilot-mcp)
- [Project Documentation](./README.md)
- [Discord Bot Setup](./INSTALL.md)
