"""Notion result models."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..model import ToolResult


@dataclass
class NotionPage(ToolResult):
    """
    Notion page information.

    Attributes:
        page_id: Page ID
        url: Page URL
        title: Page title
        created_time: Page creation time (ISO format)
        last_edited_time: Last edit time (ISO format)
        parent_type: Parent type (database_id, page_id, workspace)
        parent_id: Parent ID
        properties: Page properties as raw dict
    """

    page_id: str
    url: str
    title: str
    created_time: str
    last_edited_time: str
    parent_type: str = ""
    parent_id: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotionPageContent(ToolResult):
    """
    Notion page with full content.

    Attributes:
        page_id: Page ID
        url: Page URL
        title: Page title
        created_time: Page creation time (ISO format)
        last_edited_time: Last edit time (ISO format)
        properties: Page properties
        content: Page content blocks
    """

    page_id: str
    url: str
    title: str
    created_time: str
    last_edited_time: str
    properties: Dict[str, Any] = field(default_factory=dict)
    content: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DatabaseQueryResult(ToolResult):
    """
    Result from querying a Notion database.

    Attributes:
        results: List of page results
        has_more: Whether there are more results
        next_cursor: Cursor for pagination
        count: Number of results returned
    """

    results: List[Dict[str, Any]]
    has_more: bool
    next_cursor: Optional[str]
    count: int


@dataclass
class NotionSearchResult(ToolResult):
    """
    Result from searching Notion.

    Attributes:
        results: List of search results (pages, databases)
        total_count: Total number of results
        has_more: Whether there are more results
        next_cursor: Cursor for pagination
    """

    results: List[Dict[str, Any]]
    total_count: int
    has_more: bool
    next_cursor: Optional[str] = None


@dataclass
class NotionCommentResult(ToolResult):
    """
    Result from adding a comment to Notion.

    Attributes:
        comment_id: Comment ID
        page_id: Page ID
        text: Comment text
        created_time: Comment creation time (ISO format)
        created_by: User ID who created the comment
    """

    comment_id: str
    page_id: str
    text: str
    created_time: str
    created_by: str


@dataclass
class NotionPageUpdateResult(ToolResult):
    """
    Result from updating a Notion page.

    Attributes:
        page_id: Page ID
        url: Page URL
        last_edited_time: Last edit time (ISO format)
        properties: Updated properties
    """

    page_id: str
    url: str
    last_edited_time: str
    properties: Dict[str, Any] = field(default_factory=dict)
