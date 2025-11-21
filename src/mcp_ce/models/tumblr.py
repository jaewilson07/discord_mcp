"""Tumblr post data models for extraction and storage."""

from typing import Optional, List
from pydantic import BaseModel, Field


class TumblrPost(BaseModel):
    """
    Simplified Tumblr post for reposting to Discord.

    Focus: Extract post URL to share - Discord will auto-embed/preview it.
    """

    post_id: str = Field(
        ..., description="Unique Tumblr post identifier (e.g., '1234567890')"
    )
    post_url: str = Field(
        ..., description="Full Tumblr post URL to share (Discord will auto-preview)"
    )
    timestamp: str = Field(
        ..., description="Post timestamp in ISO format (e.g., '2025-01-01T12:00:00Z')"
    )

    # Optional metadata
    caption: Optional[str] = Field(
        None, description="Caption/comment text (optional, for reference)"
    )
    post_type: Optional[str] = Field(
        None, description="Type of post: 'image', 'gif', 'text', etc."
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase storage."""
        return {
            "post_id": self.post_id,
            "post_url": self.post_url,
            "timestamp": self.timestamp,
            "caption": self.caption,
            "post_type": self.post_type,
        }

    def to_supabase_metadata(self) -> dict:
        """Convert to metadata format for Supabase documents table."""
        return {
            "post_id": self.post_id,
            "post_url": self.post_url,
            "timestamp": self.timestamp,
            "caption": self.caption,
            "post_type": self.post_type,
        }


class TumblrPostList(BaseModel):
    """
    List of Tumblr posts extracted from a feed.

    Used as output from extraction agent when extracting multiple posts.
    """

    posts: List[TumblrPost] = Field(
        default_factory=list, description="List of extracted Tumblr posts"
    )
    total_extracted: int = Field(
        default=0, description="Total number of posts extracted"
    )
    extraction_confidence: float = Field(
        default=0.0, description="Confidence score of extraction (0.0 to 1.0)"
    )
