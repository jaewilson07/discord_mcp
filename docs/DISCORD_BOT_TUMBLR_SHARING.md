# Discord Bot Tumblr Link Sharing

This document explains how to use the Discord bot to share Tumblr links via @mentions and slash commands.

## Features

The bot supports two ways to share Tumblr links:

1. **@Mention the bot** - Mention the bot with a Tumblr URL in the message
2. **Slash command** - Use `/share_tumblr_link` command

## Usage

### Method 1: @Mention

Simply mention the bot in a Discord channel with a Tumblr URL:

```
@YourBotName https://www.tumblr.com/soyeahbluesdance
```

Or with a specific post URL:

```
@YourBotName https://www.tumblr.com/soyeahbluesdance/1234567890/post-title
```

**Behavior:**
- If you mention the bot without a Tumblr URL, it will send a help message
- If you include a Tumblr URL, it will:
  - Extract and share the post URL (if it's a direct post URL)
  - Or extract the latest post from the blog (if it's a blog URL)
  - Show a ⏳ reaction while processing
  - Show ✅ on success or ❌ on error

### Method 2: Slash Command

Use the `/share_tumblr_link` slash command:

```
/share_tumblr_link url:https://www.tumblr.com/soyeahbluesdance max_posts:5
```

**Parameters:**
- `url` (required): Tumblr blog URL or post URL
- `max_posts` (optional): Maximum number of posts to share (default: 1, max: 10)

**Examples:**
- Share a single post: `/share_tumblr_link url:https://www.tumblr.com/soyeahbluesdance/1234567890/post-title`
- Share latest 5 posts from a blog: `/share_tumblr_link url:https://www.tumblr.com/soyeahbluesdance max_posts:5`

## How It Works

1. **URL Detection**: The bot extracts Tumblr URLs from messages using regex patterns
2. **URL Type Detection**: 
   - If it's a post URL (contains numeric post ID), it shares directly
   - If it's a blog URL, it uses the `tumblr.extract_post_urls` MCP tool to scrape and extract post URLs
3. **Sharing**: Uses the `discord.send_message` MCP tool to post the URLs to the channel
4. **Discord Auto-Embedding**: Discord automatically creates rich embeds/previews for Tumblr URLs

## Supported URL Formats

- Blog URLs:
  - `https://www.tumblr.com/blogname`
  - `https://blogname.tumblr.com`
  
- Post URLs:
  - `https://www.tumblr.com/blogname/1234567890/post-title`
  - `https://blogname.tumblr.com/post/1234567890/post-title`

## MCP Tools Used

The bot uses the following MCP tools:

- `tumblr.extract_post_urls`: Extracts post URLs from Tumblr blog feeds
- `discord.send_message`: Sends messages to Discord channels

## Setup

1. Make sure your Discord bot has the required permissions:
   - Send Messages
   - Read Message History
   - Add Reactions
   - Use Slash Commands

2. Enable required intents in Discord Developer Portal:
   - MESSAGE CONTENT INTENT (required)
   - SERVER MEMBERS INTENT (required)
   - GUILDS INTENT (required)

3. **Enable Slash Commands Scope:**
   - Go to OAuth2 → URL Generator
   - Make sure `applications.commands` scope is checked
   - Re-invite the bot if needed

3. Run the bot:
   ```bash
   python run.py
   ```

4. The slash commands will be automatically synced when the bot starts

## Troubleshooting

### Slash commands not appearing

**Global Commands (Default):**
- Global commands can take **up to 1 hour** to appear in Discord
- This is a Discord API limitation, not a bug
- Commands are synced when the bot starts - check logs for confirmation

**Faster Testing - Guild-Specific Commands:**
For instant command availability during development:

1. Get your Discord server (guild) ID:
   - Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
   - Right-click your server → Copy Server ID

2. Add to your `.env` file:
   ```
   DISCORD_GUILD_ID=123456789012345678
   ```
   (Replace with your actual server ID)

3. Restart the bot - commands will sync instantly to that server

**Verify Command Sync:**
- Check bot logs for: `✅ Synced X slash command(s)`
- If you see errors, check:
  - Bot has `applications.commands` scope in OAuth2 settings
  - Bot is invited with proper permissions
  - Guild ID is correct (numeric only)

### Bot not responding to @mentions

- Check that MESSAGE CONTENT INTENT is enabled in Discord Developer Portal
- Verify the bot has permission to read messages in the channel
- Check bot logs for errors

### Tumblr links not extracting

- Verify the Tumblr URL format is correct
- Check that the blog is public and accessible
- Review bot logs for scraping errors

## Code Structure

- **Handler**: `src/mcp_ce/tools/discord/bot_handlers.py`
- **Registration**: `run.py` (handlers registered before bot starts, commands synced in `setup_hook()`)
- **MCP Tools**: 
  - `src/mcp_ce/tools/tumblr/extract_post_urls.py`
  - `src/mcp_ce/tools/discord/send_message.py`

## Implementation Notes

The implementation follows discord.py best practices:

1. **Command Registration**: Handlers are registered before the bot starts to ensure commands are available when syncing
2. **Command Syncing**: Uses `setup_hook()` (recommended by discord.py docs) instead of `on_ready()` for syncing commands
3. **Event Handling**: `on_message` properly calls `bot.process_commands(message)` to ensure prefix commands still work
4. **Bot Initialization**: Uses `commands.Bot` with proper intents configuration

