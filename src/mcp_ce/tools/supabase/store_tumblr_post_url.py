"""
Store a Tumblr post URL in Supabase for duplicate tracking.

This is a simplified version that just tracks post URLs (not full post data).
"""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from ._client_helper import get_client
from datetime import datetime


@register_command("supabase", "store_tumblr_post_url")
async def store_tumblr_post_url(
    post_url: str,
    post_id: Optional[str] = None,
    blog_name: Optional[str] = None,
    table_name: str = "tumblr_posts",
) -> ToolResponse:
    """
    Store a Tumblr post URL in Supabase for duplicate tracking.
    
    If post_id is not provided, extracts it from the URL.
    Uses upsert (INSERT ... ON CONFLICT) to avoid duplicates.
    
    Args:
        post_url: Full Tumblr post URL
        post_id: Optional Tumblr post ID (extracted from URL if not provided)
        blog_name: Optional blog name for filtering
        table_name: Name of the Supabase table (default: "tumblr_posts")
    
    Returns:
        ToolResponse containing:
        - stored: bool indicating if post was stored (or already existed)
        - post_id: The post ID used
        - is_new: bool indicating if this was a new post (True) or duplicate (False)
    """
    try:
        import re
        
        # Extract post_id from URL if not provided
        if not post_id:
            # Pattern: tumblr.com/blogname/numeric-id/...
            match = re.search(r"tumblr\.com/[^/]+/(\d+)/", post_url)
            if match:
                post_id = match.group(1)
            else:
                # Fallback: use last numeric segment
                match = re.search(r"/(\d{9,})/", post_url)
                if match:
                    post_id = match.group(1)
                else:
                    return ToolResponse(
                        is_success=False,
                        result=None,
                        error=f"Could not extract post_id from URL: {post_url}",
                    )
        
        client = get_client()
        
        # Check if post already exists
        existing = client.table(table_name).select("post_id").eq("post_id", post_id).limit(1).execute()
        
        if existing.data and len(existing.data) > 0:
            # Post already exists
            return ToolResponse(
                is_success=True,
                result={
                    "stored": True,
                    "post_id": post_id,
                    "is_new": False,
                },
            )
        
        # Insert new post (upsert to handle race conditions)
        post_data = {
            "post_id": post_id,
            "post_url": post_url,
            "post_type": "unknown",  # We don't extract type here, just track URLs
            "extracted_at": datetime.now().isoformat(),
        }
        
        if blog_name:
            post_data["original_poster"] = blog_name
        
        # Use upsert (INSERT ... ON CONFLICT DO NOTHING)
        response = client.table(table_name).upsert(
            post_data,
            on_conflict="post_id"
        ).execute()
        
        return ToolResponse(
            is_success=True,
            result={
                "stored": True,
                "post_id": post_id,
                "is_new": True,
            },
        )
        
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to store post URL: {str(e)}",
        )

