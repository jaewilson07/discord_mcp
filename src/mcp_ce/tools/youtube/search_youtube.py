"""YouTube search tool for MCP code execution server.
Searches YouTube for videos matching a topic or keywords.
"""

from datetime import datetime
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from .models import SearchResults, VideoInfo
from ._client_helper import get_client


@register_command("youtube", "search_youtube")
@cache_tool(ttl=300, id_param="query")  # Cache for 5 minutes
async def search_youtube(
    query: str,
    max_results: int = 5,
    order_by: str = "relevance",
    published_after: str = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Searches YouTube for videos matching a topic or keywords.

    Args:
        query: Search query or topic to find videos about
        max_results: Number of videos to return (1-50)
        order_by: Sort order: 'relevance', 'date', 'viewCount', or 'rating'
        published_after: ISO date string to filter videos published after this date (e.g., '2024-01-01T00:00:00Z')
        override_cache: Whether to bypass cache and force fresh search (default: False)

    Returns:
        ToolResponse with SearchResults dataclass containing:
        - query: Original search query
        - videos: List of VideoInfo dataclasses
        - count: Number of results returned
        - message: Optional message (e.g., "No videos found")
    """
    if not query.strip():
        return ToolResponse(
            is_success=False, result=None, error="Search query cannot be empty"
        )

    if order_by not in ["relevance", "date", "viewCount", "rating"]:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Invalid order_by value. Must be one of: relevance, date, viewCount, rating",
        )

    if max_results < 1 or max_results > 50:
        return ToolResponse(
            is_success=False,
            result=None,
            error="max_results must be between 1 and 50",
        )

    try:
        youtube = get_client()

        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": order_by,
            "maxResults": max_results,
        }

        if published_after:
            try:
                datetime.fromisoformat(published_after.replace("Z", "+00:00"))
                search_params["publishedAfter"] = published_after
            except ValueError:
                return ToolResponse(
                    is_success=False,
                    result=None,
                    error=f"Invalid date format for published_after. Use ISO format like '2024-01-01T00:00:00Z'",
                )

        request = youtube.search().list(**search_params)
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]

            video_info = VideoInfo(
                video_id=video_id,
                title=snippet["title"],
                description=snippet["description"],
                url=f"https://www.youtube.com/watch?v={video_id}",
                channel_title=snippet["channelTitle"],
                published_at=snippet["publishedAt"],
            )
            videos.append(video_info)

        result = SearchResults(
            query=query,
            videos=videos,
            count=len(videos),
            message=f"No videos found for query: {query}" if not videos else "",
        )

        return ToolResponse(is_success=True, result=result)

    except RuntimeError as e:
        # API key error from get_client()
        return ToolResponse(is_success=False, result=None, error=str(e))
    except Exception as e:
        return ToolResponse(
            is_success=False, result=None, error=f"Error searching YouTube: {str(e)}"
        )


if __name__ == "__main__":
    import asyncio
    import json

    # Test the tool
    result = asyncio.run(search_youtube(query="LangChain tutorial", max_results=3))
    print(json.dumps(result, indent=2))
