"""
YouTube search tool for MCP code execution server.
Searches YouTube for videos matching a topic or keywords.
"""

from googleapiclient.discovery import build
from datetime import datetime
import os
from typing import Dict, Any


async def search_youtube(
    query: str,
    max_results: int = 5,
    order_by: str = "relevance",
    published_after: str = None,
) -> Dict[str, Any]:
    """
    Searches YouTube for videos matching a topic or keywords.

    Args:
        query: Search query or topic to find videos about
        max_results: Number of videos to return (1-50)
        order_by: Sort order: 'relevance', 'date', 'viewCount', or 'rating'
        published_after: ISO date string to filter videos published after this date (e.g., '2024-01-01T00:00:00Z')

    Returns:
        dict with:
            - success: bool
            - videos: list of video metadata
            - count: number of results
            - error: error message (if failed)
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "YOUTUBE_API_KEY not found in environment variables",
        }

    if not query.strip():
        return {"success": False, "error": "Search query cannot be empty"}

    if order_by not in ["relevance", "date", "viewCount", "rating"]:
        return {
            "success": False,
            "error": f"Invalid order_by value. Must be one of: relevance, date, viewCount, rating",
        }

    if max_results < 1 or max_results > 50:
        return {"success": False, "error": "max_results must be between 1 and 50"}

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

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
                return {
                    "success": False,
                    "error": f"Invalid date format for published_after. Use ISO format like '2024-01-01T00:00:00Z'",
                }

        request = youtube.search().list(**search_params)
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]

            video_data = {
                "id": video_id,
                "title": snippet["title"],
                "description": snippet["description"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": snippet["channelTitle"],
                "published_at": snippet["publishedAt"],
            }
            videos.append(video_data)

        if not videos:
            return {
                "success": True,
                "videos": [],
                "count": 0,
                "message": f"No videos found for query: {query}",
            }

        return {"success": True, "videos": videos, "count": len(videos), "query": query}

    except Exception as e:
        return {"success": False, "error": f"Error searching YouTube: {str(e)}"}


if __name__ == "__main__":
    import asyncio
    import json

    # Test the tool
    result = asyncio.run(search_youtube(query="LangChain tutorial", max_results=3))
    print(json.dumps(result, indent=2))
