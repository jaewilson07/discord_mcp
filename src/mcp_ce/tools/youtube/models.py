"""YouTube result models."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from ..model import ToolResult


@dataclass
class Transcript(ToolResult):
    """
    Result from extracting a YouTube video transcript.

    Attributes:
        video_id: YouTube video ID (11 characters)
        transcript: Full transcript text
        language: Language code of the transcript (e.g., 'en', 'es')
        length: Character count of transcript text
        is_auto_generated: Whether transcript is auto-generated
        entries: List of individual transcript entries with timestamps
    """

    video_id: str
    transcript: str
    language: str
    length: int
    is_auto_generated: bool = False
    entries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VideoMetadata(ToolResult):
    """
    Result from extracting YouTube video metadata.

    Attributes:
        video_id: YouTube video ID
        title: Video title
        description: Video description
        channel_title: Channel name
        channel_id: Channel ID
        published_at: Publication date (ISO format)
        duration: Video duration (ISO 8601 format)
        view_count: Number of views
        like_count: Number of likes
        comment_count: Number of comments
        tags: List of video tags
        category_id: Video category ID
        url: Full YouTube URL
    """

    video_id: str
    title: str = ""
    description: str = ""
    channel_title: str = ""
    channel_id: str = ""
    published_at: str = ""
    duration: str = ""
    view_count: str = "0"
    like_count: str = "0"
    comment_count: str = "0"
    tags: List[str] = field(default_factory=list)
    category_id: str = ""
    url: str = ""


@dataclass
class VideoInfo(ToolResult):
    """
    Individual video information from search results.

    Attributes:
        video_id: YouTube video ID
        title: Video title
        description: Video description
        url: Full YouTube URL
        channel_title: Channel name
        published_at: Publication date (ISO format)
    """

    video_id: str
    title: str
    description: str
    url: str
    channel_title: str
    published_at: str


@dataclass
class SearchResults(ToolResult):
    """
    Result from YouTube search query.

    Attributes:
        query: Original search query
        videos: List of video results
        count: Number of results returned
        message: Optional message (e.g., "No videos found")
    """

    query: str
    videos: List[VideoInfo]
    count: int
    message: str = ""
