"""Retrieve a document from Supabase by ID."""

from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.supabase.models import Document
from ._client_helper import get_client


@register_command("supabase", "get_document")
@cache_tool(ttl=300, id_param="document_id")  # Cache for 5 minutes
async def get_document(
    document_id: str,
    table_name: str = "documents",
    override_cache: bool = False,
) -> ToolResponse:
    """
    Retrieve a document from Supabase by its ID.
    
    Args:
        document_id: The UUID of the document to retrieve
        table_name: Name of the Supabase table (default: "documents")
        override_cache: Whether to bypass cache and force fresh query (default: False)
    
    Returns:
        ToolResponse containing:
        - Document object with all fields (id, url, title, content, metadata, etc.)
    """
    try:
        client = get_client()
        
        # Query document by ID
        response = client.table(table_name).select("*").eq("id", document_id).execute()
        
        if not response.data or len(response.data) == 0:
            return ToolResponse(
                is_success=False,
                result=None,
                error=f"Document with ID '{document_id}' not found"
            )
        
        # Extract the document
        doc_data = response.data[0]
        
        # Create Document result object
        document = Document(
            id=str(doc_data.get("id", "")),
            url=doc_data.get("url", ""),
            title=doc_data.get("title", ""),
            content=doc_data.get("content", ""),
            description=doc_data.get("description", ""),
            author=doc_data.get("author", ""),
            published_date=doc_data.get("published_date", ""),
            keywords=doc_data.get("keywords", []),
            metadata=doc_data.get("metadata", {}),
            created_at=doc_data.get("created_at", ""),
            updated_at=doc_data.get("updated_at", ""),
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
            error=f"Failed to retrieve document: {str(e)}"
        )

