# Tumblr Feed Supabase Setup Guide

This guide explains how to set up the Supabase storage schema for the Tumblr Feed workflow.

## Overview

The Tumblr Feed workflow stores posts in Supabase to:
- Track which posts have been scraped
- Enable duplicate checking
- Store post metadata for Discord posting
- Track sync history

## Schema Setup

### Option 1: Using Supabase Dashboard (Recommended)

1. **Open Supabase Dashboard**
   - Go to your Supabase project
   - Navigate to SQL Editor

2. **Run the Migration**
   - Copy the contents of `docs/supabase/tumblr_feed_schema.sql`
   - Paste into SQL Editor
   - Click "Run" to execute

3. **Verify Table Creation**
   - Go to Table Editor
   - You should see `tumblr_posts` table
   - Check that indexes are created

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Link to your project
supabase link --project-ref your-project-ref

# Run migration
supabase db push
```

### Option 3: Using Existing `documents` Table

If you prefer to use the existing `documents` table with metadata:

The current `add_document` tool already supports storing Tumblr posts in the `metadata` field:

```python
metadata = {
    "post_id": "tumblr_post_id",
    "post_type": "image",
    "image_urls": ["url1", "url2"],
    "original_poster": "username",
    "post_url": "https://...",
    "timestamp": "2025-01-01T00:00:00Z",
    "tags": ["tag1", "tag2"],
}
```

However, for better querying and indexing, the dedicated `tumblr_posts` table is recommended.

## Schema Details

### Table: `tumblr_posts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `post_id` | TEXT | Unique Tumblr post ID (indexed) |
| `post_type` | TEXT | Post type: 'text', 'image', 'gif', 'reblog' |
| `content` | TEXT | Post text content |
| `image_urls` | JSONB | Array of image/GIF URLs |
| `original_poster` | TEXT | Username if reblogged |
| `post_url` | TEXT | Full Tumblr post URL |
| `timestamp` | TIMESTAMPTZ | Original post timestamp |
| `tags` | JSONB | Array of tags |
| `likes` | INTEGER | Number of likes |
| `reblogs` | INTEGER | Number of reblogs |
| `extracted_at` | TIMESTAMPTZ | When post was extracted |
| `created_at` | TIMESTAMPTZ | Record creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

### Indexes

- `idx_tumblr_posts_post_id` - Fast duplicate checking
- `idx_tumblr_posts_timestamp` - Sorting by post date
- `idx_tumblr_posts_post_type` - Filtering by type
- `idx_tumblr_posts_extracted_at` - Tracking sync history

## Querying Posts

### Check for Duplicate

```sql
SELECT * FROM tumblr_posts WHERE post_id = 'tumblr_post_id_123';
```

### Get Recent Posts

```sql
SELECT * FROM tumblr_posts 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Get Posts by Type

```sql
SELECT * FROM tumblr_posts 
WHERE post_type = 'image' 
ORDER BY timestamp DESC;
```

### Get Posts Since Last Sync

```sql
SELECT * FROM tumblr_posts 
WHERE extracted_at > '2025-01-01T00:00:00Z'
ORDER BY extracted_at DESC;
```

## Using in Code

### Using Dedicated Table

Update `sync_tumblr_feed.py` to use `tumblr_posts` table:

```python
doc_result = await add_document(
    url=post_url,
    title=f"Tumblr Post {post_id}",
    content=post_content,
    table_name="tumblr_posts",  # Use dedicated table
    metadata={
        "post_id": post_id,
        "post_type": post_type,
        # ... other fields
    }
)
```

### Using Metadata in Existing Table

Current implementation uses metadata field:

```python
doc_result = await add_document(
    url=post_url,
    title=f"Tumblr Post {post_id}",
    content=post_content,
    table_name="documents",  # Existing table
    metadata={
        "source": "tumblr_feed",
        "post_id": post_id,
        "post_type": post_type,
        # ... other fields
    }
)
```

## Security

The schema includes Row Level Security (RLS). Adjust policies based on your needs:

- **Public access**: Current policy allows all operations
- **Authenticated only**: Uncomment the authenticated policy
- **Custom policies**: Create specific policies for your use case

## Troubleshooting

### Table Already Exists

If you get "relation already exists" error:
- Drop the table first: `DROP TABLE IF EXISTS tumblr_posts CASCADE;`
- Or use `CREATE TABLE IF NOT EXISTS` (already in migration)

### Index Creation Fails

If indexes fail to create:
- Check that the table exists first
- Verify you have proper permissions
- Check Supabase logs for detailed errors

### Duplicate Checking Not Working

Ensure:
- `post_id` has UNIQUE constraint
- Index on `post_id` is created
- Query uses exact `post_id` match

## Next Steps

After setting up the schema:
1. ✅ Test duplicate checking
2. ✅ Verify post storage
3. ✅ Test queries
4. ✅ Update `sync_tumblr_feed` to use the schema
5. ✅ Test end-to-end workflow

