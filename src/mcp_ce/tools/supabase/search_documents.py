"""Search for documents in Supabase using text search or filters."""

from typing import Optional, Dict, Any
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.supabase.models import DocumentSearchResult
from ._client_helper import get_client


@register_command("supabase", "search_documents")
@cache_tool(ttl=180, id_param="query")  # Cache for 3 minutes
async def search_documents(
    query: Optional[str] = None,
    table_name: str = "documents",
    limit: int = 10,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Search for documents in Supabase.
    
    This tool supports:
    - Text search across title, content, and description fields
    - Filtering by metadata fields
    - Pagination with limit and offset
    
    Args:
        query: Text search query (searches in title, content, description)
        table_name: Name of the Supabase table (default: "documents")
        limit: Maximum number of results to return (default: 10, max: 100)
        offset: Number of results to skip for pagination (default: 0)
        filters: Optional dictionary of filters (e.g., {"author": "John Doe"})
        override_cache: Whether to bypass cache and force fresh search (default: False)
    
    Returns:
        ToolResponse containing:
        - DocumentSearchResult with list of matching documents
        - count: Number of results returned
    """
    try:
        client = get_client()
        
        # Limit the maximum results
        limit = min(limit, 100)
        
        # Build the query
        query_builder = client.table(table_name).select("*")
        
        # Apply text search if query provided
        if query:
            # Search across multiple columns using ilike (case-insensitive pattern matching)
            # PostgREST or_() syntax: "column1.ilike.pattern,column2.ilike.pattern"
            # Pattern should include % for partial matching
            search_pattern = f"%{query}%"
            # Use or_() to search across title, content, and description
            query_builder = query_builder.or_(
                f"title.ilike.{search_pattern},content.ilike.{search_pattern},description.ilike.{search_pattern}"
            )
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    query_builder = query_builder.in_(key, value)
                else:
                    query_builder = query_builder.eq(key, value)
        
        # Apply pagination
        query_builder = query_builder.limit(limit).offset(offset)
        
        # Execute query
        response = query_builder.execute()
        
        # Get results
        results = response.data if response.data else []
        
        # Format results as dictionaries
        formatted_results = []
        for doc_data in results:
            formatted_results.append({
                "id": str(doc_data.get("id", "")),
                "url": doc_data.get("url", ""),
                "title": doc_data.get("title", ""),
                "content": doc_data.get("content", "")[:500] + "..." if len(doc_data.get("content", "")) > 500 else doc_data.get("content", ""),  # Truncate content for search results
                "description": doc_data.get("description", ""),
                "author": doc_data.get("author", ""),
                "published_date": doc_data.get("published_date", ""),
                "keywords": doc_data.get("keywords", []),
                "metadata": doc_data.get("metadata", {}),
                "created_at": doc_data.get("created_at", ""),
                "updated_at": doc_data.get("updated_at", ""),
            })
        
        # Create search result object
        search_result = DocumentSearchResult(
            results=formatted_results,
            count=len(formatted_results),
        )
        
        return ToolResponse(
            is_success=True,
            result=search_result,
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
            error=f"Failed to search documents: {str(e)}"
        )

