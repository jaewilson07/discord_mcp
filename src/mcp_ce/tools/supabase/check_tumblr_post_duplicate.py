"""Check if a Tumblr post already exists in Supabase (for duplicate checking)."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from ._client_helper import get_client


@register_command("supabase", "check_tumblr_post_duplicate")
async def check_tumblr_post_duplicate(
    post_id: str,
    table_name: str = "tumblr_posts",
) -> ToolResponse:
    """
    Check if a Tumblr post with the given post_id already exists.
    
    This is used for duplicate checking before storing new posts.
    
    Args:
        post_id: The Tumblr post ID to check
        table_name: Name of the Supabase table (default: "tumblr_posts")
    
    Returns:
        ToolResponse containing:
        - exists: bool indicating if post exists
        - post_data: dict with post data if found, None otherwise
    """
    try:
        client = get_client()
        
        # Query for post by post_id
        response = client.table(table_name).select("*").eq("post_id", post_id).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            post_data = response.data[0]
            return ToolResponse(
                is_success=True,
                result={
                    "exists": True,
                    "post_data": post_data,
                },
            )
        else:
            return ToolResponse(
                is_success=True,
                result={
                    "exists": False,
                    "post_data": None,
                },
            )
            
    except RuntimeError as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=str(e)
        )
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to check duplicate: {str(e)}"
        )

