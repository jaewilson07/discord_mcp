# Daily Tumblr Sync to Discord

## Overview

Automated daily workflow that:
1. Extracts post URLs from configured Tumblr blogs
2. Checks Supabase for duplicates (prevents reposting)
3. Stores new posts in Supabase
4. Reposts new posts to Discord with automatic channel routing

## Setup

### 1. Supabase Table

The `tumblr_posts` table should already exist. If not, run the migration:

```bash
# Run the SQL migration in your Supabase dashboard
# Or use the Supabase CLI:
supabase db push docs/supabase/tumblr_feed_schema.sql
```

See `docs/supabase/tumblr_feed_schema.sql` for the full schema.

### 2. Environment Variables

Ensure these are set:
- `DISCORD_TOKEN` or `DISCORD_BOT_TOKEN` - Discord bot token
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service role key
- `DISCORD_DEV_MODE` (optional) - Set to `"true"` for DEV channels

### 3. Configure Blogs

Edit `src/mcp_ce/agentic_tools/graphs/tumblr_feed/daily_sync_tumblr_to_discord.py`:

```python
TUMBLR_BLOGS = [
    {
        "url": "https://www.tumblr.com/soyeahbluesdance",
        "name": "soyeahbluesdance",
    },
    {
        "url": "https://ohyeahswingdance.tumblr.com",
        "name": "ohyeahswingdance",
    },
]
```

## Running the Sync

### Manual Run

```bash
python scripts/run_daily_tumblr_sync.py
```

### GitHub Actions (Recommended)

The workflow is already configured in `.github/workflows/daily-tumblr-sync.yml`.

**Setup:**
1. Add secrets to your GitHub repository:
   - `DISCORD_TOKEN`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

2. The workflow runs daily at 9:00 AM UTC (adjust in the cron schedule)

3. You can also trigger manually via GitHub Actions UI

### Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM):
0 9 * * * /path/to/python /path/to/scripts/run_daily_tumblr_sync.py >> /path/to/logs/tumblr_sync.log 2>&1
```

### Systemd Timer (Linux)

Create `/etc/systemd/system/tumblr-sync.service`:
```ini
[Unit]
Description=Daily Tumblr Sync to Discord
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/mcp-discord
Environment="DISCORD_TOKEN=your-token"
Environment="SUPABASE_URL=your-url"
Environment="SUPABASE_KEY=your-key"
ExecStart=/path/to/python /path/to/scripts/run_daily_tumblr_sync.py
```

Create `/etc/systemd/system/tumblr-sync.timer`:
```ini
[Unit]
Description=Run Tumblr sync daily
Requires=tumblr-sync.service

[Timer]
OnCalendar=daily
OnCalendar=09:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable tumblr-sync.timer
sudo systemctl start tumblr-sync.timer
```

## How It Works

1. **Extract Posts**: Uses `extract_post_urls` to scrape each configured blog
2. **Check Duplicates**: Queries Supabase `tumblr_posts` table by `post_id`
3. **Store New Posts**: Inserts new post URLs into Supabase
4. **Repost to Discord**: Uses `repost_tumblr` which automatically:
   - Routes to correct Discord channel based on blog name
   - Creates channels if needed (e.g., ohyeahswingdance)
   - Posts the URL (Discord auto-embeds)

## Monitoring

The script outputs detailed logs:
- Posts found per blog
- New posts detected
- Posts successfully posted
- Errors (if any)

Check logs regularly to ensure the sync is working.

## Troubleshooting

### No posts found
- Blog might be private or require authentication
- Blog URL format might be incorrect
- Tumblr might have changed their page structure

### Duplicate posts
- Check Supabase table - `post_id` should be unique
- Verify the duplicate check is working

### Discord posting fails
- Check bot token and permissions
- Verify channel IDs in `repost_tumblr` routing config
- Check rate limits (script waits 2s between posts)

## Supabase Table Schema

The `tumblr_posts` table tracks:
- `post_id` (unique) - Tumblr post ID for duplicate checking
- `post_url` - Full Tumblr post URL
- `post_type` - Type of post
- `extracted_at` - When we extracted this post
- `created_at` - When stored in Supabase

See `docs/supabase/tumblr_feed_schema.sql` for full schema.

## Note on Table Creation

**Supabase MCP doesn't have a table creation tool** - you need to:
1. Use the Supabase dashboard SQL editor
2. Use the Supabase CLI
3. Run migrations manually

The schema is provided in `docs/supabase/tumblr_feed_schema.sql`.

