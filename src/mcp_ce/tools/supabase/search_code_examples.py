"""Search for code examples in Supabase (deterministic search tool)."""

from typing import Optional, Dict, Any
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.supabase.models import CodeExampleSearchResult
from ._client_helper import get_client


@register_command("supabase", "search_code_examples")
@cache_tool(ttl=180, id_param="query")  # Cache for 3 minutes
async def search_code_examples(
    query: Optional[str] = None,
    language: Optional[str] = None,
    table_name: str = "code_examples",
    limit: int = 10,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Search for code examples in Supabase.
    
    This is a DETERMINISTIC tool that searches stored code examples.
    It does NOT use AI - it's a pure search function.
    
    This tool supports:
    - Text search across code, summary, and context fields
    - Language filtering
    - Metadata filtering
    - Pagination
    
    Args:
        query: Text search query (searches in code, summary, context)
        language: Filter by programming language (e.g., 'python', 'javascript')
        table_name: Name of the Supabase table (default: "code_examples")
        limit: Maximum number of results to return (default: 10, max: 100)
        offset: Number of results to skip for pagination (default: 0)
        filters: Optional dictionary of metadata filters (e.g., {"function_name": "get_user"})
        override_cache: Whether to bypass cache and force fresh search (default: False)
    
    Returns:
        ToolResponse containing:
        - CodeExampleSearchResult with list of matching code examples
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
            search_pattern = f"%{query}%"
            # Search across code, summary, and context
            query_builder = query_builder.or_(
                f"code.ilike.{search_pattern},summary.ilike.{search_pattern},context.ilike.{search_pattern}"
            )
        
        # Apply language filter if provided
        if language:
            query_builder = query_builder.eq("language", language)
        
        # Apply metadata filters if provided
        if filters:
            for key, value in filters.items():
                # For metadata fields, use JSONB path queries
                if key.startswith("metadata."):
                    # Extract the metadata key
                    metadata_key = key.replace("metadata.", "")
                    query_builder = query_builder.eq(f"metadata->>{metadata_key}", value)
                else:
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
        for example_data in results:
            formatted_results.append({
                "id": str(example_data.get("id", "")),
                "source_url": example_data.get("source_url", ""),
                "code": example_data.get("code", ""),
                "language": example_data.get("language", ""),
                "summary": example_data.get("summary", ""),
                "context": example_data.get("context", ""),
                "metadata": example_data.get("metadata", {}),
                "created_at": example_data.get("created_at", ""),
                "updated_at": example_data.get("updated_at", ""),
            })
        
        # Create search result object
        search_result = CodeExampleSearchResult(
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
            error=f"Failed to search code examples: {str(e)}"
        )

