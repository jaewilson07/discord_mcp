"""Add a document to Supabase (typically from crawl4ai scraping)."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.supabase.models import Document
from ._client_helper import get_client


@register_command("supabase", "add_document")
async def add_document(
    url: str,
    title: str,
    content: str,
    description: str = "",
    author: str = "",
    published_date: str = "",
    keywords: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    table_name: str = "documents",
) -> ToolResponse:
    """
    Add a document to Supabase database.
    
    This tool stores documents scraped by crawl4ai or other sources into Supabase.
    The document is stored with metadata including URL, title, content, and optional fields.
    
    Args:
        url: The source URL of the document
        title: Document title
        content: Document content (markdown or text)
        description: Document description/summary (default: "")
        author: Document author (default: "")
        published_date: Publication date in ISO format (default: "")
        keywords: List of keywords/tags (default: None)
        metadata: Additional metadata as dictionary (default: None)
        table_name: Name of the Supabase table to store documents (default: "documents")
    
    Returns:
        ToolResponse containing:
        - Document object with id, url, title, content, and metadata
        - created_at timestamp
    """
    try:
        client = get_client()
        
        # Prepare document data
        now = datetime.now().isoformat()
        document_data = {
            "url": url,
            "title": title,
            "content": content,
            "description": description,
            "author": author,
            "published_date": published_date,
            "keywords": keywords or [],
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }
        
        # Insert document into Supabase
        response = client.table(table_name).insert(document_data).execute()
        
        if not response.data:
            return ToolResponse(
                is_success=False,
                result=None,
                error="Failed to insert document: No data returned"
            )
        
        # Extract the inserted document
        inserted_doc = response.data[0] if isinstance(response.data, list) else response.data
        
        # Create Document result object
        document = Document(
            id=str(inserted_doc.get("id", "")),
            url=inserted_doc.get("url", url),
            title=inserted_doc.get("title", title),
            content=inserted_doc.get("content", content),
            description=inserted_doc.get("description", description),
            author=inserted_doc.get("author", author),
            published_date=inserted_doc.get("published_date", published_date),
            keywords=inserted_doc.get("keywords", keywords or []),
            metadata=inserted_doc.get("metadata", metadata or {}),
            created_at=inserted_doc.get("created_at", now),
            updated_at=inserted_doc.get("updated_at", now),
        )
        
        return ToolResponse(
            is_success=True,
            result=document,
        )
        
    except RuntimeError as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=str(e)
        )
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Failed to add document: {str(e)}"
        )

