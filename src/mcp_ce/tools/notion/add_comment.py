"""Add a comment to a Notion page."""

from registry import register_command
from mcp_ce.tools.model import ToolResponse
from .models import NotionCommentResult
from ._client_helper import get_client


@register_command("notion", "add_notion_comment")
async def add_notion_comment(page_id: str, comment_text: str) -> ToolResponse:
    """
    Add a comment to a Notion page.

    Args:
        page_id: The ID of the page to add a comment to
        comment_text: The text content of the comment to add

    Returns:
        ToolResponse with NotionCommentResult dataclass containing:
        - comment_id: Comment ID
        - page_id: Page ID
        - text: Comment text
        - created_time: Creation time
        - created_by: User ID who created the comment
    """
    try:
        client = get_client()

        # Create comment using Notion API
        response = await client.comments.create(
            parent={"page_id": page_id},
            rich_text=[{"type": "text", "text": {"content": comment_text}}],
        )

        result = NotionCommentResult(
            comment_id=response["id"],
            page_id=page_id,
            text=comment_text,
            created_time=response.get("created_time", ""),
            created_by=response.get("created_by", {}).get("id", ""),
        )

        return ToolResponse(is_success=True, result=result)

    except RuntimeError as e:
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False, result=None, error=f"Error adding comment: {str(e)}"
        )


# Test code
if __name__ == "__main__":
    import asyncio
    import sys

    async def test():
        if len(sys.argv) > 2:
            result = await add_notion_comment(sys.argv[1], sys.argv[2])

            print(f"Success: {result['success']}")
            if result["success"]:
                print(f"Comment ID: {result['comment_id']}")
            else:
                print(f"Error: {result['error']}")
        else:
            print("Usage: python add_comment.py <page_id> <comment_text>")

    asyncio.run(test())
