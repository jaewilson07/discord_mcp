"""
Code Summarization Agent.

This agent uses AI to generate summaries of code examples.
It's an AGENTIC tool (uses AI), not a deterministic tool.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .._model_helper import _get_model

logger = logging.getLogger(__name__)


# ===== Models =====


class CodeSummaryResult(BaseModel):
    """Result from code summarization."""

    summary: str = Field(description="Concise summary of what the code does")
    purpose: str = Field(description="The main purpose or goal of the code")
    key_concepts: list[str] = Field(
        default_factory=list, description="Key programming concepts used"
    )
    complexity: str = Field(
        description="Complexity level: 'simple', 'moderate', or 'complex'"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the summary accuracy"
    )


# ===== Dependencies =====


@dataclass
class CodeSummarizationDeps:
    """Dependencies for code summarization."""

    code: str
    language: str
    context: Optional[str] = None  # Optional context about where code was found


# ===== Agent Definition =====


code_summarizer_agent = Agent[CodeSummarizationDeps, CodeSummaryResult](
    _get_model("code_summarizer"),
    output_type=CodeSummaryResult,
    system_prompt="""You are an expert code analyst specializing in understanding and summarizing code.

Your job is to analyze code snippets and provide:
1. A concise summary of what the code does
2. The main purpose or goal
3. Key programming concepts used
4. Complexity assessment
5. Confidence in your analysis

Be accurate and specific. Focus on what the code actually does, not what it might do.""",
)


@code_summarizer_agent.tool
async def analyze_code_structure(
    ctx: RunContext[CodeSummarizationDeps],
) -> str:
    """Analyze the structure of the code (functions, classes, imports, etc.)."""
    code = ctx.deps.code
    language = ctx.deps.language

    try:
        logfire.info("Analyzing code structure", language=language)

        # Basic structure analysis
        lines = code.split("\n")
        total_lines = len(lines)

        # Count common patterns
        has_imports = any(
            line.strip().startswith(("import ", "from ")) for line in lines
        )
        has_functions = "def " in code or "function " in code
        has_classes = "class " in code
        has_async = "async " in code

        structure_info = f"""Code Structure Analysis:
- Total lines: {total_lines}
- Has imports: {has_imports}
- Has functions: {has_functions}
- Has classes: {has_classes}
- Uses async: {has_async}
- Language: {language}
"""

        if ctx.deps.context:
            structure_info += f"\nContext: {ctx.deps.context}"

        logfire.info("Code structure analysis complete")
        return structure_info

    except Exception as e:
        logger.error(f"Code structure analysis error: {e}")
        return f"Error analyzing code structure: {str(e)}"


# ===== Public API =====


async def summarize_code(
    code: str,
    language: str,
    context: Optional[str] = None,
) -> CodeSummaryResult:
    """
    Summarize code using AI.
    
    This is an AGENTIC function (uses AI) that generates code summaries.
    For deterministic code extraction, use the extract_code_blocks tool.
    
    Args:
        code: The code to summarize
        language: Programming language (e.g., 'python', 'javascript')
        context: Optional context about where code was found
        
    Returns:
        CodeSummaryResult with summary, purpose, key_concepts, complexity, confidence
    """
    deps = CodeSummarizationDeps(code=code, language=language, context=context)

    result = await code_summarizer_agent.run(
        f"Analyze and summarize this {language} code",
        deps=deps,
    )

    return result.data

