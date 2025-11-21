# Tumblr Repost Tool

## Overview

The `repost_tumblr` Discord tool automatically routes Tumblr posts to the correct Discord channels based on the Tumblr blog name.

## Usage

```python
from mcp_ce.tools.discord.repost_tumblr import repost_tumblr

# Post a Tumblr URL - automatically routes to correct channel
result = await repost_tumblr(
    tumblr_url="https://www.tumblr.com/soyeahbluesdance/777551231593988096/...",
    dev_mode=False,  # Use PROD channel
)
```

## Channel Routing

### Configured Blogs

1. **soyeahbluesdance**
   - PROD: Channel ID `1441205355995463822` ("so yeah, blues dance")
   - DEV: Channel ID `1439978275517763684` (bot testing channel)
   - Routing: Uses PROD channel by default, DEV channel if `dev_mode=True`

2. **ohyeahswingdance**
   - Channel: Automatically creates/finds channel named "ohyeahswingdance"
   - Routing: Uses `upsert_text_channel` to find or create the channel

## URL Format Support

The tool supports both Tumblr URL formats:

- **Path format**: `https://www.tumblr.com/blogname/postid/...`
- **Subdomain format**: `https://blogname.tumblr.com/post/...`

## Implementation Details

- **Tool**: `src/mcp_ce/tools/discord/repost_tumblr.py`
- **Registration**: `@register_command("discord", "repost_tumblr")`
- **Dependencies**: 
  - `send_message` - Posts the URL to Discord
  - `upsert_text_channel` - Creates/finds channels for blogs that need them

## Configuration

Channel routing is configured in `TUMBLR_BLOG_ROUTING` dictionary:

```python
TUMBLR_BLOG_ROUTING = {
    "soyeahbluesdance": {
        "prod_channel_id": "1441205355995463822",
        "dev_channel_id": "1439978275517763684",
    },
    "ohyeahswingdance": {
        "channel_name": "ohyeahswingdance",
    },
}
```

## Testing

Run the test script:

```bash
python test_repost_tumblr.py
```

This tests:
1. DEV mode routing for soyeahbluesdance
2. PROD mode routing for soyeahbluesdance
3. Channel creation/finding for ohyeahswingdance

## Deprecated Code

The following files have been deprecated in favor of this simpler tool:

- `src/mcp_ce/agentic_tools/graphs/tumblr_feed/repost_tumblr_to_discord.py` - Complex extraction workflow (kept for reference)
- `src/mcp_ce/agentic_tools/graphs/tumblr_feed/repost_tumblr_urls.py` - Updated to use `repost_tumblr` tool

