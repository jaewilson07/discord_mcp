"""
YouTube video metadata tool for MCP code execution server.
Retrieves detailed metadata for a specific YouTube video.
"""

from googleapiclient.discovery import build
import os
import re
from typing import Dict, Any


async def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """
    Retrieves detailed metadata for a specific YouTube video including title, description,
    duration, tags, channel info, and statistics.

    Args:
        video_id: YouTube video ID (11 characters) or full URL

    Returns:
        dict with:
            - success: bool
            - video_id: str
            - title: str
            - description: str
            - channel: str
            - channel_id: str
            - published_at: str
            - tags: list of str
            - category_id: str
            - duration: str (ISO 8601 duration format)
            - view_count: str
            - like_count: str
            - comment_count: str
            - url: str
            - error: error message (if failed)
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "YOUTUBE_API_KEY not found in environment variables",
        }

    if not video_id.strip():
        return {"success": False, "error": "video_id cannot be empty"}

    # Extract video ID from URL if needed
    extracted_id = _extract_video_id(video_id)

    if not extracted_id or len(extracted_id) != 11:
        return {"success": False, "error": "Invalid video ID. Must be 11 characters"}

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        request = youtube.videos().list(
            part="snippet,contentDetails,statistics", id=extracted_id
        )
        response = request.execute()

        if not response.get("items"):
            return {
                "success": False,
                "error": f"No video found with ID: {extracted_id}",
            }

        video = response["items"][0]
        snippet = video["snippet"]
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        return {
            "success": True,
            "video_id": extracted_id,
            "title": snippet["title"],
            "description": snippet["description"],
            "channel": snippet["channelTitle"],
            "channel_id": snippet["channelId"],
            "published_at": snippet["publishedAt"],
            "tags": snippet.get("tags", []),
            "category_id": snippet.get("categoryId", "Unknown"),
            "duration": content_details.get("duration", "Unknown"),
            "view_count": statistics.get("viewCount", "N/A"),
            "like_count": statistics.get("likeCount", "N/A"),
            "comment_count": statistics.get("commentCount", "N/A"),
            "url": f"https://www.youtube.com/watch?v={extracted_id}",
        }

    except Exception as e:
        return {"success": False, "error": f"Error retrieving video metadata: {str(e)}"}


def _extract_video_id(input_str: str) -> str:
    """
    Extracts 11-character video ID from various YouTube URL formats or direct ID.
    """
    input_str = input_str.strip()

    # Check if it's already a valid 11-character ID
    if len(input_str) == 11 and input_str.isalnum():
        return input_str

    # Try various URL patterns
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)

    return None


if __name__ == "__main__":
    import asyncio
    import json

    # Test the tool
    result = asyncio.run(get_video_metadata(video_id="dQw4w9WgXcQ"))
    print(json.dumps(result, indent=2))
