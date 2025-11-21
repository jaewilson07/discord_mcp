"""Add a code example to Supabase (deterministic storage tool)."""

from typing import Optional, Dict, Any
from datetime import datetime
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.supabase.models import CodeExample
from ._client_helper import get_client


@register_command("supabase", "add_code_example")
async def add_code_example(
    source_url: str,
    code: str,
    language: str,
    summary: str = "",
    context: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    table_name: str = "code_examples",
) -> ToolResponse:
    """
    Add a code example to Supabase database.
    
    This is a DETERMINISTIC tool that stores code examples.
    It does NOT use AI - it's a pure storage function.
    
    For AI-powered code summarization, use an agent that:
    1. Extracts code blocks using extract_code_blocks tool
    2. Uses an AI agent to generate summaries
    3. Calls this tool to store the code with summary
    
    Args:
        source_url: The URL where the code was found
        code: The code content
        language: Programming language (e.g., 'python', 'javascript')
        summary: AI-generated summary of the code (optional, can be added by agent)
        context: Context where code was found (e.g., section title, function name)
        metadata: Additional metadata (function_name, class_name, etc.)
        table_name: Name of the Supabase table (default: "code_examples")
    
    Returns:
        ToolResponse containing:
        - CodeExample object with id, source_url, code, language, summary, etc.
        - created_at timestamp
    """
    try:
        client = get_client()
        
        # Prepare code example data
        now = datetime.now().isoformat()
        code_example_data = {
            "source_url": source_url,
            "code": code,
            "language": language,
            "summary": summary,
            "context": context,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }
        
        # Insert code example into Supabase
        response = client.table(table_name).insert(code_example_data).execute()
        
        if not response.data:
            return ToolResponse(
                is_success=False,
                result=None,
                error="Failed to insert code example: No data returned"
            )
        
        # Extract the inserted code example
        inserted_example = response.data[0] if isinstance(response.data, list) else response.data
        
        # Create CodeExample result object
        code_example = CodeExample(
            id=str(inserted_example.get("id", "")),
            source_url=inserted_example.get("source_url", source_url),
            code=inserted_example.get("code", code),
            language=inserted_example.get("language", language),
            summary=inserted_example.get("summary", summary),
            context=inserted_example.get("context", context),
            metadata=inserted_example.get("metadata", metadata or {}),
            created_at=inserted_example.get("created_at", now),
            updated_at=inserted_example.get("updated_at", now),
        )
        
        return ToolResponse(
            is_success=True,
            result=code_example,
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
            error=f"Failed to add code example: {str(e)}"
        )

