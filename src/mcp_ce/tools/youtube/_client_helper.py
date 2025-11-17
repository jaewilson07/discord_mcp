"""
YouTube API client helper for managing YouTube Data API v3 resource.

Provides singleton access to the YouTube API client with API key management.
"""

import os
from typing import Optional
from googleapiclient.discovery import build, Resource


_youtube_client: Optional[Resource] = None


def get_client() -> Resource:
    """
    Get or create YouTube Data API v3 client instance.

    Returns:
        YouTube API Resource object for making API calls

    Raises:
        RuntimeError: If YOUTUBE_API_KEY environment variable is not set

    Example:
        youtube = get_client()
        request = youtube.videos().list(part="snippet", id="video_id")
        response = request.execute()
    """
    global _youtube_client

    if _youtube_client is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "YOUTUBE_API_KEY not found in environment variables. "
                "Please set YOUTUBE_API_KEY in your .env file."
            )

        _youtube_client = build("youtube", "v3", developerKey=api_key)

    return _youtube_client


def reset_client() -> None:
    """
    Reset the YouTube client instance.

    Useful for testing or when API key changes.
    """
    global _youtube_client
    _youtube_client = None
