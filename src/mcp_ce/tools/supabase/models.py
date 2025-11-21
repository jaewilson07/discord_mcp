"""Supabase document result models."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..model import ToolResult


@dataclass
class Document(ToolResult):
    """
    Document stored in Supabase.
    
    Attributes:
        id: Document ID (UUID)
        url: Source URL of the document
        title: Document title
        content: Document content (markdown or text)
        description: Document description/summary
        author: Document author (if available)
        published_date: Publication date (if available)
        keywords: List of keywords/tags
        metadata: Additional metadata as dict
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update
    """
    
    id: str
    url: str
    title: str
    content: str
    description: str = ""
    author: str = ""
    published_date: str = ""
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class DocumentSearchResult(ToolResult):
    """
    Result from searching documents in Supabase.
    
    Attributes:
        results: List of matching documents
        count: Number of results returned
        total_count: Total number of matching documents (if available)
    """
    
    results: List[Dict[str, Any]]
    count: int
    total_count: Optional[int] = None


@dataclass
class CodeExample(ToolResult):
    """
    Code example stored in Supabase.
    
    Attributes:
        id: Code example ID (UUID)
        source_url: Source URL where code was found
        code: The code content
        language: Programming language
        summary: AI-generated summary (if available)
        context: Context where code was found (e.g., section title)
        metadata: Additional metadata (function name, class name, etc.)
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update
    """
    
    id: str
    source_url: str
    code: str
    language: str
    summary: str = ""
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class CodeExampleSearchResult(ToolResult):
    """
    Result from searching code examples in Supabase.
    
    Attributes:
        results: List of matching code examples
        count: Number of results returned
        total_count: Total number of matching examples (if available)
    """
    
    results: List[Dict[str, Any]]
    count: int
    total_count: Optional[int] = None