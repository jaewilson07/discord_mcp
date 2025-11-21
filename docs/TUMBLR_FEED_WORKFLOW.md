# Tumblr Feed Recreation Workflow

## Overview

This workflow recreates the Tumblr feed from `https://www.tumblr.com/soyeahbluesdance` by:

1. Scraping the Tumblr blog feed
2. Extracting posts (images, GIFs, text, reblogs)
3. Storing posts in Supabase
4. Posting to Discord channels
5. Running on a schedule to check for new content

## Architecture

```
┌─────────────────┐
│  Tumblr Feed    │
│  (soyeahblues)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Crawl4AI       │
│  Scraper        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extraction     │
│  Agent          │
│  (Posts/GIFs)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Supabase       │
│  Storage        │
│  (Post DB)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Discord        │
│  Posting        │
│  (Channel)      │
└─────────────────┘
```

## Workflow Steps

### 1. Scrape Tumblr Feed

- **Tool**: `crawl_website` (crawl4ai)
- **URL**: `https://www.tumblr.com/soyeahbluesdance`
- **Configuration**:
  - `extract_images: true` - Get all images/GIFs
  - `extract_links: true` - Get reblog links
  - `js_code`: Scroll to load lazy content
  - `wait_for_selector`: Wait for post container

### 2. Extract Posts

- **Agent**: Custom extraction agent
- **Extract**:
  - Post type (text, image, GIF, reblog)
  - Post content/text
  - Image/GIF URLs
  - Original poster (if reblog)
  - Post timestamp
  - Tags/categories
  - Engagement metrics (likes, reblogs)

### 3. Store in Supabase

- **Tool**: `add_document` (supabase)
- **Schema**:
  ```json
  {
    "post_id": "tumblr_post_id",
    "post_type": "image|text|gif|reblog",
    "content": "post text",
    "image_urls": ["url1", "url2"],
    "original_poster": "username",
    "post_url": "tumblr_url",
    "timestamp": "ISO datetime",
    "tags": ["tag1", "tag2"],
    "likes": 123,
    "reblogs": 45,
    "extracted_at": "ISO datetime"
  }
  ```

### 4. Post to Discord

- **Tool**: `send_message` (discord)
- **Channel**: Target Discord channel
- **Format**:
  - Text posts: Send as message
  - Image/GIF posts: Send with image attachment
  - Reblogs: Include attribution

### 5. Deduplication

- Check Supabase for existing `post_id`
- Skip if already posted
- Track last sync timestamp

## Implementation

### Workflow Graph

```python
# src/mcp_ce/agentic_tools/graphs/tumblr_feed/tumblr_feed_workflow.py

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class TumblrPost(BaseModel):
    """Tumblr post structure"""
    post_id: str
    post_type: str  # text, image, gif, reblog
    content: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    original_poster: Optional[str] = None
    post_url: str
    timestamp: str
    tags: List[str] = Field(default_factory=list)
    likes: int = 0
    reblogs: int = 0

class TumblrFeedWorkflowDeps(BaseModel):
    """Workflow dependencies"""
    tumblr_url: str = "https://www.tumblr.com/soyeahbluesdance"
    discord_channel_id: Optional[str] = None
    discord_server_id: Optional[str] = None
    supabase_source: str = "tumblr_feed"
    max_posts: int = 10
    check_duplicates: bool = True
```

### Main Workflow Function

```python
async def sync_tumblr_feed(
    tumblr_url: str = "https://www.tumblr.com/soyeahbluesdance",
    discord_channel_id: Optional[str] = None,
    discord_server_id: Optional[str] = None,
    max_posts: int = 10,
    check_duplicates: bool = True,
) -> Dict[str, Any]:
    """
    Sync Tumblr feed to Discord channel.

    Workflow:
    1. Scrape Tumblr feed
    2. Extract posts
    3. Check for duplicates in Supabase
    4. Store new posts in Supabase
    5. Post to Discord channel
    """
    results = {
        "success": False,
        "posts_scraped": 0,
        "posts_extracted": 0,
        "posts_new": 0,
        "posts_posted": 0,
        "errors": [],
    }

    try:
        # Step 1: Scrape Tumblr feed
        from mcp_ce.tools.crawl4ai.crawl_website import crawl_website

        scrape_result = await crawl_website(
            url=tumblr_url,
            extract_images=True,
            extract_links=True,
            word_count_threshold=5,
            headless=True,
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            wait_for_selector="article",
        )

        if not scrape_result.is_success:
            results["errors"].append(f"Scraping failed: {scrape_result.error}")
            return results

        # Step 2: Extract posts using extraction agent
        from mcp_ce.tools.agents.extraction_agent_tool import extraction_agent_tool

        content = scrape_result.result.get("content_markdown", "")
        extraction_result = await extraction_agent_tool(
            content=content,
            extraction_type="tumblr_post",
            context={"url": tumblr_url, "max_posts": max_posts},
        )

        if not extraction_result.is_success:
            results["errors"].append(f"Extraction failed: {extraction_result.error}")
            return results

        posts = extraction_result.result.items
        results["posts_extracted"] = len(posts)

        # Step 3: Check duplicates and store in Supabase
        from mcp_ce.tools.supabase.add_document import add_document
        from mcp_ce.tools.supabase.search_documents import search_documents

        new_posts = []
        for post in posts:
            post_id = post.get("post_id") or post.get("url", "")

            if check_duplicates:
                # Check if post already exists
                search_result = await search_documents(
                    source=supabase_source,
                    query=f"post_id:{post_id}",
                    limit=1,
                )

                if search_result.is_success and search_result.result.get("documents"):
                    continue  # Skip duplicate

            # Store in Supabase
            doc_result = await add_document(
                source=supabase_source,
                content=post.get("content", ""),
                metadata={
                    "post_id": post_id,
                    "post_type": post.get("post_type"),
                    "image_urls": post.get("image_urls", []),
                    "original_poster": post.get("original_poster"),
                    "post_url": post.get("post_url"),
                    "timestamp": post.get("timestamp"),
                    "tags": post.get("tags", []),
                },
            )

            if doc_result.is_success:
                new_posts.append(post)
                results["posts_new"] += 1

        # Step 4: Post to Discord
        if discord_channel_id and new_posts:
            from mcp_ce.tools.discord.send_message import send_message

            for post in new_posts:
                # Format message
                message = format_tumblr_post(post)

                # Send to Discord
                msg_result = await send_message(
                    channel_id=discord_channel_id,
                    content=message,
                )

                if msg_result.is_success:
                    results["posts_posted"] += 1
                else:
                    results["errors"].append(f"Failed to post {post.get('post_id')}: {msg_result.error}")

        results["success"] = True
        return results

    except Exception as e:
        results["errors"].append(str(e))
        return results

def format_tumblr_post(post: Dict[str, Any]) -> str:
    """Format Tumblr post for Discord"""
    lines = []

    # Attribution
    if post.get("original_poster"):
        lines.append(f"**Reblogged from @{post['original_poster']}**")

    # Content
    if post.get("content"):
        lines.append(post["content"])

    # Images
    if post.get("image_urls"):
        for img_url in post["image_urls"]:
            lines.append(img_url)

    # Tags
    if post.get("tags"):
        tags = " ".join([f"#{tag}" for tag in post["tags"]])
        lines.append(f"\n{tags}")

    # Link
    if post.get("post_url"):
        lines.append(f"\n🔗 {post['post_url']}")

    return "\n".join(lines)
```

## Scheduling

### Option 1: Cron Job

```bash
# Run every 6 hours
0 */6 * * * cd /path/to/mcp-discord && uv run python -m src.mcp_ce.agentic_tools.graphs.tumblr_feed.sync_tumblr_feed
```

### Option 2: Discord Bot Command

```python
@bot.command(name="sync_tumblr")
async def sync_tumblr(ctx, channel_id: str = None):
    """Manually sync Tumblr feed"""
    channel = channel_id or ctx.channel.id
    result = await sync_tumblr_feed(
        discord_channel_id=channel,
        discord_server_id=ctx.guild.id,
    )
    await ctx.send(f"✅ Synced {result['posts_posted']} new posts!")
```

### Option 3: Periodic Task (asyncio)

```python
async def periodic_sync(interval_hours: int = 6):
    """Run periodic sync"""
    while True:
        await sync_tumblr_feed()
        await asyncio.sleep(interval_hours * 3600)
```

## Configuration

### Environment Variables

```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Discord
DISCORD_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=target_channel_id

# Tumblr (optional, for API access)
TUMBLR_API_KEY=your_api_key
```

## Data Schema

### Supabase Document Structure

```json
{
  "id": "uuid",
  "source": "tumblr_feed",
  "content": "Post text content",
  "metadata": {
    "post_id": "tumblr_post_123",
    "post_type": "image",
    "image_urls": ["https://..."],
    "original_poster": "username",
    "post_url": "https://soyeahbluesdance.tumblr.com/post/123",
    "timestamp": "2024-01-01T12:00:00Z",
    "tags": ["blues", "dance", "meme"],
    "likes": 123,
    "reblogs": 45
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Next Steps

1. **Set up Linear project** - See `TUMBLR_FEED_LINEAR_PLAN.md` for issue breakdown
2. **Create extraction schema** for Tumblr posts
3. **Implement workflow graph** using Pydantic-AI
4. **Set up Supabase table** for post storage
5. **Create Discord channel** for feed
6. **Test scraping** Tumblr feed
7. **Implement scheduling** mechanism
8. **Add error handling** and retry logic
9. **Monitor and log** sync activity

## Linear Project Tracking

This project is tracked in Linear. See `docs/TUMBLR_FEED_LINEAR_PLAN.md` for:

- Complete issue breakdown
- Phase-by-phase implementation plan
- Acceptance criteria for each task
- Script to create Linear issues automatically

To create Linear issues:

```bash
# Set your Linear API key
export LINEAR_API_KEY=your_key_here

# Run the script
python scripts/create_linear_issues.py
```
