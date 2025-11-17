"""
YouTube video metadata tool for MCP code execution server.
Retrieves detailed metadata for a specific YouTube video.
"""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import VideoMetadata
from ._utils import extract_video_id as _extract_video_id
from ._client_helper import get_client


@register_command("youtube", "get_video_metadata")
@cache_tool(ttl=3600, id_param="video_id")  # Cache for 1 hour
async def get_video_metadata(
    video_id: str, override_cache: bool = False
) -> ToolResponse:
    """
    Retrieves detailed metadata for a specific YouTube video including title, description,
    duration, tags, channel info, and statistics.

    Args:
        video_id: YouTube video ID (11 characters) or full URL
        override_cache: Whether to bypass cache and force fresh fetch (default: False)

    Returns:
        ToolResponse with VideoMetadata dataclass containing:
        - video_id: YouTube video ID
        - title: Video title
        - description: Video description
        - channel_title: Channel name
        - channel_id: Channel ID
        - published_at: Publication date (ISO format)
        - tags: List of video tags
        - category_id: Video category ID
        - duration: Video duration (ISO 8601 format)
        - view_count: Number of views
        - like_count: Number of likes
        - comment_count: Number of comments
        - url: Full YouTube URL
    """
    if not video_id.strip():
        return ToolResponse(
            is_success=False, result=None, error="video_id cannot be empty"
        )

    # Extract video ID from URL if needed
    extracted_id = _extract_video_id(video_id)

    if not extracted_id or len(extracted_id) != 11:
        return ToolResponse(
            is_success=False,
            result=None,
            error="Invalid video ID. Must be 11 characters",
        )

    try:
        youtube = get_client()

        request = youtube.videos().list(
            part="snippet,contentDetails,statistics", id=extracted_id
        )
        response = request.execute()

        if not response.get("items"):
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"No video found with ID: {extracted_id}",
            )

        video = response["items"][0]
        snippet = video["snippet"]
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        result = VideoMetadata(
            video_id=extracted_id,
            title=snippet["title"],
            description=snippet["description"],
            channel_title=snippet["channelTitle"],
            channel_id=snippet["channelId"],
            published_at=snippet["publishedAt"],
            tags=snippet.get("tags", []),
            category_id=snippet.get("categoryId", "Unknown"),
            duration=content_details.get("duration", "Unknown"),
            view_count=statistics.get("viewCount", "0"),
            like_count=statistics.get("likeCount", "0"),
            comment_count=statistics.get("commentCount", "0"),
            url=f"https://www.youtube.com/watch?v={extracted_id}",
        )

        return ToolResponse(is_success=True, result=result)

    except RuntimeError as e:
        # API key error from get_client()
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Error retrieving video metadata: {str(e)}",
        )


if __name__ == "__main__":
    import asyncio
    import json

    # Test the tool
    result = asyncio.run(get_video_metadata(video_id="dQw4w9WgXcQ"))
    print(json.dumps(result, indent=2))
