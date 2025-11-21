"""Tool wrapper for code summarization agent (agentic tool)."""

from typing import Optional
from registry import register_command
from mcp_ce.tools.model import ToolResponse
from mcp_ce.agentic_tools.agents.code_summarizer import (
    summarize_code,
    CodeSummaryResult,
)


@register_command("agents", "code_summarizer")
async def code_summarizer_tool(
    code: str,
    language: str,
    context: Optional[str] = None,
) -> ToolResponse:
    """
    Generate an AI-powered summary of code.
    
    This is an AGENTIC tool (uses AI) that analyzes and summarizes code.
    
    For deterministic code extraction (no AI), use:
    - extract_code_blocks (crawl4ai) - extracts code from markdown
    - add_code_example (supabase) - stores code examples
    
    This tool is useful for:
    - Generating summaries for code examples before storage
    - Understanding code snippets in documentation
    - Creating code documentation
    
    Args:
        code: The code to summarize
        language: Programming language (e.g., 'python', 'javascript', 'typescript')
        context: Optional context about where code was found (e.g., section title, function name)
        
    Returns:
        ToolResponse containing:
        - summary: Concise summary of what the code does
        - purpose: The main purpose or goal of the code
        - key_concepts: List of key programming concepts used
        - complexity: Complexity level ('simple', 'moderate', or 'complex')
        - confidence: Confidence score (0.0 to 1.0)
    """
    try:
        result = await summarize_code(code=code, language=language, context=context)
        
        return ToolResponse(
            is_success=True,
            result=result,
        )
        
    except Exception as e:
        return ToolResponse(
            is_success=False,
            result=None,
            error=f"Code summarization failed: {str(e)}"
        )

