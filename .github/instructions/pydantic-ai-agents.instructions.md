applyTo: "src/mcp_ce/agents/**/*.py,src/mcp_ce/agentic_tools/agents/**/*.py"
---

# Pydantic-AI Agent Design Guide for MCP Discord Project

This guide provides comprehensive instructions for designing and implementing AI agents using the Pydantic-AI framework in the MCP Discord project. It combines patterns from the official pydantic-ai library with proven practices from the Archon framework.

## Table of Contents

1. [Quick Start Example](#quick-start-example)
2. [Overview](#overview)
3. [Architecture Principles](#architecture-principles)
4. [Agent Structure](#agent-structure)
5. [Dependency Injection Pattern](#dependency-injection-pattern)
6. [Tool Design](#tool-design)
7. [System Prompts](#system-prompts)
8. [Structured Output](#structured-output)
9. [Complete Agent Examples](#complete-agent-examples)
10. [Testing Agents](#testing-agents)
11. [Best Practices](#best-practices)

## Quick Start Example

Below is a simple Pydantic-AI agent that demonstrates the core pattern. This triage assistant integrates with a mock database to fetch patient information and vital signs.

**Key Pattern Elements:**
- **Dataclasses** for dependencies and data models
- **Pydantic BaseModel** for agent output
- **@agent.tool** for callable functions
- **@agent.system_prompt** for dynamic prompts
- **RunContext** for accessing dependencies

```python
from dataclasses import dataclass
from typing import Any
import asyncio

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv

load_dotenv()

# Step 1: Define data models (dataclasses for entities)
@dataclass
class Patient:
    id: int
    name: str
    vitals: dict[str, Any]

PATIENT_DB = {
    42: Patient(id=42, name="John Doe", vitals={"heart_rate": 72, "blood_pressure": "120/80"}),
    43: Patient(id=43, name="Jane Smith", vitals={"heart_rate": 65, "blood_pressure": "110/70"}),
}

class DatabaseConn:
    async def patient_name(self, id: int) -> str:
        patient = PATIENT_DB.get(id)
        return patient.name if patient else "Unknown Patient"

    async def latest_vitals(self, id: int) -> dict[str, Any]:
        patient = PATIENT_DB.get(id)
        return patient.vitals if patient else {"heart_rate": 0, "blood_pressure": "N/A"}

# Step 2: Define dependencies (dataclass for injection)
@dataclass
class TriageDependencies:
    patient_id: int
    db: DatabaseConn

# Step 3: Define output schema (Pydantic BaseModel for validation)
class TriageOutput(BaseModel):
    response_text: str = Field(description="Message to the patient")
    escalate: bool = Field(description="Should escalate to a human nurse")
    urgency: int = Field(description="Urgency level from 0 to 10", ge=0, le=10)

# Step 4: Create agent with tools and prompts
triage_agent = Agent(
    "openai:gpt-4o",
    deps_type=TriageDependencies,
    output_type=TriageOutput,
    system_prompt=(
        "You are a triage assistant helping patients. "
        "Provide clear advice and assess urgency."
    ),
)

@triage_agent.system_prompt
async def add_patient_name(ctx: RunContext[TriageDependencies]) -> str:
    """Dynamic system prompt - adds patient context."""
    patient_name = await ctx.deps.db.patient_name(id=ctx.deps.patient_id)
    return f"The patient's name is {patient_name!r}."

@triage_agent.tool
async def latest_vitals(ctx: RunContext[TriageDependencies]) -> dict[str, Any]:
    """Returns the patient's latest vital signs."""
    return await ctx.deps.db.latest_vitals(id=ctx.deps.patient_id)

# Step 5: Run the agent
async def main() -> None:
    deps = TriageDependencies(patient_id=43, db=DatabaseConn())

    result = await triage_agent.run(
        "I have chest pain and trouble breathing.",
        deps=deps,
    )
    print(result.output)
    # Output: TriageOutput(response_text='Your symptoms are serious...', escalate=True, urgency=10)

    result = await triage_agent.run(
        "I have a mild headache since yesterday.",
        deps=deps,
    )
    print(result.output)
    # Output: TriageOutput(response_text='It sounds like...', escalate=False, urgency=3)
```

**What This Example Shows:**
- ✅ Dependency injection pattern (database connection)
- ✅ Dynamic system prompts (patient name added at runtime)
- ✅ Tools that access dependencies via `ctx.deps`
- ✅ Structured output with Pydantic validation
- ✅ Type-safe agent configuration

## Overview

**What is Pydantic-AI?**
Pydantic-AI is a Python agent framework that brings FastAPI-like developer experience to Generative AI applications. It leverages Pydantic for type-safe structured outputs and provides model-agnostic support for LLMs.

**When to Use Agents vs Tools:**
- **Tools** (MCP CE tools): Single atomic operations (API calls, database queries, file operations)
- **Agents**: Complex workflows requiring LLM reasoning, multi-step orchestration, or natural language processing

**Key Benefits:**
- Type-safe dependency injection
- Structured, validated outputs using Pydantic models
- Tool composition via `@agent.tool` decorator
- Dynamic system prompts with `RunContext`
- Async/await support throughout
- Model-agnostic design (OpenAI, Anthropic, Google, etc.)

## Architecture Principles

### 1. Base Agent Pattern (Archon-Inspired)

All agents in this project inherit from `BaseAgent` to provide:
- **Error handling and retries** - Automatic retry logic for transient failures
- **Rate limiting protection** - OpenAI rate limit handling with exponential backoff
- **Logging and monitoring** - Standardized logging across all agents
- **Standard dependency injection** - Type-safe dependency pattern
- **Common utilities** - Shared helper functions and decorators

**File Location:** `src/mcp_ce/agents/base_agent.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar
from pydantic import BaseModel
from pydantic_ai import Agent

@dataclass
class AgentDependencies:
    """Base dependencies for all agents."""
    request_id: str | None = None
    user_id: str | None = None
    trace_id: str | None = None

DepsT = TypeVar("DepsT", bound=AgentDependencies)
OutputT = TypeVar("OutputT")

class BaseAgent(ABC, Generic[DepsT, OutputT]):
    """
    Base class for all Pydantic-AI agents.
    
    Provides common functionality:
    - Error handling and retries
    - Rate limiting protection
    - Logging and monitoring
    - Standard dependency injection
    """
    
    def __init__(
        self,
        model: str = "openai:gpt-4o",
        name: str = None,
        retries: int = 3,
        enable_rate_limiting: bool = True,
        **agent_kwargs,
    ):
        self.model = model
        self.name = name or self.__class__.__name__
        self.retries = retries
        self._agent = self._create_agent(**agent_kwargs)
    
    @abstractmethod
    def _create_agent(self, **kwargs) -> Agent:
        """Create and configure the Pydantic-AI agent."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        pass
    
    async def run(self, user_prompt: str, deps: DepsT) -> OutputT:
        """Run the agent with rate limiting and error handling."""
        # Implementation handles retries, rate limits, etc.
        pass
```

### 2. Workflow Specs (mcp-agent–Inspired)

Instead of scattering configuration across code, define **explicit workflow specs** that describe each agent in a single place and then use that spec to build your Pydantic-AI agent. This mirrors the `AgentSpec` / workflow pattern in `mcp-agent` ([mcp-agent README](https://github.com/lastmile-ai/mcp-agent)).

**Goals:**
- Centralize **name, description, inputs, outputs, toolsets, and MCP servers**.
- Make it easy to **inspect, test, and re-use** agent workflows.
- Keep the **agent constructor thin** – all behavior is described in the spec.

```python
from dataclasses import dataclass
from typing import Literal, Sequence
from pydantic import BaseModel

from .base_agent import AgentDependencies, BaseAgent


@dataclass
class AgentWorkflowSpec:
    """High-level description of an agent workflow (mcp-agent-inspired)."""

    name: str
    description: str
    model: str
    input_type: type[BaseModel]
    output_type: type[BaseModel]
    mcp_servers: Sequence[str]  # logical names like "github", "context7"
    tools: Sequence[str]        # logical tool names, not functions
    mode: Literal["planner", "executor", "router"] = "executor"


class WorkflowAgent(BaseAgent[AgentDependencies, BaseModel]):
    """
    Base class for workflow-driven agents.

    Concrete agents:
    - Define a WorkflowSpec
    - Implement _create_agent() to register tools based on that spec
    """

    def __init__(self, spec: AgentWorkflowSpec):
        self.spec = spec
        super().__init__(model=spec.model, name=spec.name)

    def get_system_prompt(self) -> str:
        return (
            f"You are '{self.spec.name}'. {self.spec.description}\n\n"
            "You MUST treat the workflow spec as the source of truth for:\n"
            "- Required inputs and outputs\n"
            "- Allowed tools\n"
            "- Overall mode (planner, executor, router)."
        )
```

**When adding new agents:**
- Prefer **defining a spec object** first, then the agent class.
- Keep system prompts **aligned with the spec fields**.
- Use `mode="planner"` for **routing / planning agents** that call other agents.

### 3. Work Orders (Archon Agent-Work-Orders–Inspired)

For complex, multi-step tasks, structure inputs as a **WorkOrder** model instead of a raw string prompt. This pattern is inspired by Archon’s `agent-work-orders` commands.

**Benefits:**
- Clear separation between **task description**, **constraints**, **artifacts**, and **acceptance criteria**.
- Easier to **log and replay** work.
- Enables **manager/worker agent setups**.

```python
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkArtifact(BaseModel):
    name: str
    description: str
    path: Optional[str] = Field(
        default=None,
        description="Repository-relative path for code/docs to create or update.",
    )


class WorkOrder(BaseModel):
    """Top-level work order for manager/worker-style agents."""

    title: str = Field(description="Short, action-oriented title.")
    goal: str = Field(description="What success looks like from the user's POV.")
    background: str = Field(
        description="Relevant context, links, and prior decisions."
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Hard constraints (APIs, performance, security, etc.).",
    )
    deliverables: List[WorkArtifact] = Field(
        description="Concrete artifacts this work order must produce.",
    )
    non_goals: List[str] = Field(
        default_factory=list,
        description="Things explicitly out of scope.",
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Checklist used to decide if work is complete.",
    )
```

**Pattern:**
- **Manager agent**: Takes a `WorkOrder`, decomposes it into steps, and orchestrates tools / sub-agents.
- **Worker agents**: Take **narrower inputs** (e.g., “implement function X in file Y under constraint Z”) and focus on execution.

Guidelines:
- For any task touching multiple files or systems, **prefer a WorkOrder** over a free-form string.
- Always include **explicit acceptance criteria** so agents can self-check before returning.

### 4. MCP Integration for Pydantic-AI Agents

Pydantic-AI has first-class MCP client support ([Pydantic-AI MCP client docs](https://ai.pydantic.dev/mcp/client/?utm_source=openai)). Use this to give agents access to:
- Local code tools (e.g., `mcp-code-execution` in this repo).
- External services (`github`, `context7`, `Notion` from `.cursor/mcp.json`).

**Client setup (conceptual example):**

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP


github_server = MCPServerStreamableHTTP("https://api.githubcopilot.com/mcp/")
context7_server = MCPServerStreamableHTTP("https://mcp.context7.com/mcp")

agent = Agent(
    model="openai:gpt-4o",
    deps_type=MyDependencies,
    result_type=MyOutput,
    toolsets=[github_server, context7_server],
    system_prompt="You are a repo-aware assistant that uses MCP tools.",
)
```

**Project-specific guidance:**
- Prefer **MCP tools** (via `mcp-code-execution`, `github`, `context7`, `Notion`) over ad-hoc HTTP calls where possible.
- Document **which MCP servers a given agent is allowed to use** in its workflow spec.
- For agents that operate over this repo’s code, **always consult**:
  - `IMPLEMENTATION_PLAN.md` for architecture and migration guidance.
  - `.github/instructions/*.md` for repo-specific conventions.


### 2. Data Models Pattern

**Key Distinction:** Tools vs Agents use different model types.

| Aspect | Tool Result Models | Agent Output Models |
|--------|-------------------|---------------------|
| **Type** | `@dataclass` extending `ToolResult` | `BaseModel` from Pydantic |
| **Purpose** | Deterministic API/DB responses | LLM-generated validated outputs |
| **Validation** | Type hints only | Runtime validation with Pydantic |
| **Use Case** | `get_video_metadata` → `VideoMetadata` | `analyze_video` → `VideoAnalysis` |

**Example:**

```python
# TOOL: Deterministic result (dataclass)
from dataclasses import dataclass

@dataclass
class VideoMetadata(ToolResult):
    video_id: str
    title: str
    channel: str
    duration: int

# AGENT: LLM-generated result (Pydantic BaseModel)
from pydantic import BaseModel, Field

class VideoAnalysis(BaseModel):
    key_topics: List[str] = Field(description="Main topics discussed")
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str = Field(min_length=100)
    urgency: int = Field(ge=0, le=10)
```

## Agent Structure

### Complete Agent Template

```python
"""
Brief description of agent capabilities.

Example: YouTube Video Analysis Agent - Analyzes YouTube videos using
transcript extraction and LLM-powered analysis.
"""

import logging
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base_agent import AgentDependencies, BaseAgent

logger = logging.getLogger(__name__)

# Step 1: Define dependencies (dataclass)
@dataclass
class VideoAnalysisDependencies(AgentDependencies):
    """
    Dependencies for video analysis operations.
    
    Attributes:
        video_id: YouTube video ID to analyze
        db_connection: Database connection for storing results
        api_key: YouTube API key for metadata access
    """
    video_id: str
    db_connection: Any  # Or specific type
    api_key: str

# Step 2: Define structured output (Pydantic BaseModel)
class VideoAnalysisResult(BaseModel):
    """
    LLM-generated analysis result.
    
    This model validates LLM output using Pydantic validation rules.
    """
    video_title: str
    key_topics: List[str] = Field(description="Main topics discussed")
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str = Field(min_length=100, description="Detailed summary")
    highlights: List[str] = Field(description="Key highlights with timestamps")
    urgency: int = Field(ge=0, le=10, description="Content urgency level")

# Step 3: Implement agent class
class VideoAnalysisAgent(BaseAgent[VideoAnalysisDependencies, VideoAnalysisResult]):
    """
    Agent for analyzing YouTube videos.
    
    Capabilities:
    - Fetch video metadata and transcripts
    - Perform semantic analysis on content
    - Extract key topics and sentiment
    - Generate structured summaries
    """
    
    def __init__(self, model: str = None, **kwargs):
        """Initialize the video analysis agent."""
        super().__init__(
            model=model or "openai:gpt-4o",
            name="VideoAnalysisAgent",
            **kwargs,
        )
    
    def _create_agent(self, **kwargs) -> Agent:
        """Create the Pydantic-AI agent with tools and prompts."""
        
        agent = Agent(
            model=self.model,
            deps_type=VideoAnalysisDependencies,
            result_type=VideoAnalysisResult,
            system_prompt=self.get_system_prompt(),
            **kwargs,
        )
        
        # Register tools
        @agent.tool
        async def get_video_metadata(
            ctx: RunContext[VideoAnalysisDependencies]
        ) -> dict:
            """Fetch video metadata from YouTube API."""
            # Use ctx.deps to access dependencies
            api_key = ctx.deps.api_key
            video_id = ctx.deps.video_id
            # Implementation...
            return {"title": "...", "duration": 120}
        
        @agent.tool
        async def get_transcript(
            ctx: RunContext[VideoAnalysisDependencies]
        ) -> str:
            """Get video transcript."""
            video_id = ctx.deps.video_id
            # Implementation...
            return "Transcript text..."
        
        return agent
    
    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        return """You are a YouTube Video Analysis Expert.

Your Capabilities:
- Analyze video transcripts and extract key topics
- Assess sentiment and tone
- Generate comprehensive summaries
- Identify highlights and important moments

Your Approach:
1. Use get_video_metadata tool to understand context
2. Use get_transcript tool to get full content
3. Analyze content for topics, sentiment, and highlights
4. Generate structured analysis following the output schema

Always provide specific examples and timestamp references."""
```

## Dependency Injection Pattern

### Why Dependency Injection?

**Benefits:**
- Type-safe access to external resources (databases, APIs, clients)
- Testable (inject mocks during testing)
- Modular (dependencies defined separately from logic)
- Clear contract (explicit requirements via type hints)

### Dependency Dataclass Structure

```python
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class MyAgentDependencies(AgentDependencies):
    """
    Dependencies for MyAgent.
    
    All dependencies are injected at runtime via the `deps` parameter.
    """
    # Required dependencies (no default)
    database: DatabaseConnection
    api_key: str
    
    # Optional dependencies (with defaults)
    cache_ttl: int = 3600
    max_retries: int = 3
    
    # Callbacks for progress updates
    progress_callback: Optional[Callable] = None
    
    # Feature flags
    enable_caching: bool = True
```

### Accessing Dependencies in Tools

```python
@agent.tool
async def fetch_user_data(
    ctx: RunContext[MyAgentDependencies],
    user_id: str
) -> dict:
    """
    Fetch user data from database.
    
    Args:
        ctx: Runtime context with injected dependencies
        user_id: User ID to fetch
        
    Returns:
        User data dictionary
    """
    # Access dependencies via ctx.deps
    db = ctx.deps.database
    cache_ttl = ctx.deps.cache_ttl
    
    # Use dependencies
    user = await db.get_user(user_id)
    
    # Progress callback (if provided)
    if ctx.deps.progress_callback:
        await ctx.deps.progress_callback({
            "step": "fetch_user",
            "user_id": user_id,
        })
    
    return user
```

### Running Agent with Dependencies

```python
async def main():
    # Create dependencies
    deps = MyAgentDependencies(
        database=DatabaseConnection(...),
        api_key="sk-...",
        cache_ttl=7200,
        progress_callback=lambda msg: print(f"Progress: {msg}"),
    )
    
    # Run agent
    agent = MyAgent()
    result = await agent.run("Analyze user behavior", deps=deps)
    print(result)
```

## Tool Design

### Tool Registration with @agent.tool

**Key Principle:** Tools are functions decorated with `@agent.tool` that the LLM can call.

### Tool Pattern

```python
@agent.tool
async def tool_name(
    ctx: RunContext[DependenciesType],
    param1: str,
    param2: int = 10,
) -> str:
    """
    Brief description of what the tool does.
    
    The docstring is passed to the LLM as the tool description.
    Use clear, action-oriented language.
    
    Args:
        ctx: Runtime context (DO NOT include in LLM schema)
        param1: Description of parameter (appears in LLM schema)
        param2: Optional parameter with default (appears in LLM schema)
        
    Returns:
        Description of return value
    """
    # Access dependencies
    deps = ctx.deps
    
    # Implement tool logic
    result = await some_operation(param1, param2)
    
    # Return string (tools should return strings or JSON-serializable dicts)
    return result
```

### Tool Guidelines

1. **Clear Docstrings**: The docstring becomes the tool description for the LLM
2. **Type Hints**: All parameters must have type hints (Pydantic validates them)
3. **RunContext First**: Always first parameter (not seen by LLM)
4. **Return Strings**: Tools should return strings or JSON-serializable objects
5. **Error Handling**: Handle errors gracefully and return error messages
6. **Stateless**: Tools should not modify agent state

### Tool Examples from Archon

**Example 1: Database Query Tool**
```python
@agent.tool
async def search_documents(
    ctx: RunContext[RagDependencies],
    query: str,
    source_filter: str | None = None
) -> str:
    """Search through documents using semantic search."""
    try:
        # Use dependency (MCP client)
        mcp_client = await get_mcp_client()
        
        # Perform search
        result = await mcp_client.perform_rag_query(
            query=query,
            source_id=source_filter or ctx.deps.source_filter,
            match_count=ctx.deps.match_count,
        )
        
        # Parse and format results
        if result.get("success"):
            matches = result.get("matches", [])
            return format_search_results(matches)
        else:
            return f"Search failed: {result.get('error')}"
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Error searching documents: {str(e)}"
```

**Example 2: Document Creation Tool**
```python
@agent.tool
async def create_document(
    ctx: RunContext[DocumentDependencies],
    title: str,
    document_type: str,
    content_description: str,
) -> str:
    """Create a new document with structured content."""
    try:
        # Progress callback
        if ctx.deps.progress_callback:
            await ctx.deps.progress_callback({
                "step": "creating_document",
                "title": title,
            })
        
        # Generate document structure
        blocks = generate_document_blocks(title, document_type, content_description)
        
        # Create via service
        doc_id = await document_service.create(
            project_id=ctx.deps.project_id,
            title=title,
            blocks=blocks,
        )
        
        return f"Successfully created document '{title}' (ID: {doc_id})"
    except Exception as e:
        return f"Failed to create document: {str(e)}"
```

### Code-First Tool Execution (Cloudflare Code Mode–Inspired)

For **very complex tool orchestration**, consider a “code mode” where the agent writes **code that calls a stable tool API**, rather than invoking many tools directly in natural language. This pattern is inspired by Cloudflare’s *Code Mode* approach ([Cloudflare Code Mode blog](https://blog.cloudflare.com/code-mode/)).

**Pattern:**
- Define a **small, typed Python (or TypeScript) API** that wraps MCP CE tools (e.g., `run_ping(url)`, `get_discord_channel(id)`).
- Have an agent whose primary output is **code** against that API (e.g., a Python function body or script).
- Execute the generated code in a **sandboxed environment** (e.g., via `mcp-code-execution`) and feed back results.

Use this mode when:
- The task requires **non-trivial branching, loops, or stateful orchestration** across many tools.
- You want a clear, reviewable artifact (code) that encodes the workflow.
- You need easier debugging and iteration than “opaque” chains of tool calls.

### Tool Composition (Calling Other Tools)

**IMPORTANT:** Tools can call other tools' underlying functions (not via LLM).

```python
@agent.tool
async def analyze_video_comprehensive(
    ctx: RunContext[VideoAnalysisDependencies]
) -> str:
    """Perform comprehensive video analysis."""
    
    # Call other tools' functions directly (NOT via LLM)
    metadata = await get_video_metadata(ctx)
    transcript = await get_transcript(ctx)
    
    # Process combined data
    analysis = f"Title: {metadata['title']}\nTranscript: {transcript[:100]}..."
    return analysis
```

## System Prompts

### Static System Prompts

Defined during agent initialization:

```python
agent = Agent(
    model="openai:gpt-4o",
    deps_type=MyDependencies,
    system_prompt="""You are an Expert Data Analyst.

Your Capabilities:
- Analyze datasets and identify patterns
- Generate statistical summaries
- Create data visualizations
- Provide actionable insights

Your Approach:
1. Understand the data structure
2. Identify key metrics
3. Analyze trends and anomalies
4. Generate clear recommendations""",
)
```

### Dynamic System Prompts

Use `@agent.system_prompt` decorator to add context-aware prompts:

```python
@agent.system_prompt
async def add_user_context(ctx: RunContext[MyDependencies]) -> str:
    """Add dynamic user context to system prompt."""
    user_name = await ctx.deps.database.get_user_name(ctx.deps.user_id)
    return f"The user's name is {user_name}."

@agent.system_prompt
def add_timestamp() -> str:
    """Add current timestamp (non-async)."""
    return f"Current time: {datetime.now().isoformat()}"
```

### System Prompt Best Practices

1. **Clear Role Definition**: "You are a [specific role]..."
2. **Capability List**: What the agent can do
3. **Approach/Methodology**: How the agent should work
4. **Common Query Examples**: Show how to use tools
5. **Response Guidelines**: Output format, citation rules, etc.

**Example from Archon RagAgent:**

```python
system_prompt="""You are a RAG Assistant that helps users search documentation.

**Your Capabilities:**
- Search through crawled documentation
- Filter searches by sources
- Find code examples
- Synthesize information from multiple sources

**Your Approach:**
1. **Understand the query** - Interpret user's intent
2. **Search effectively** - Use appropriate tools and filters
3. **Analyze results** - Review retrieved content
4. **Synthesize answers** - Combine information
5. **Cite sources** - Always reference source documents

**Common Queries:**
- "What resources are available?" → Use list_available_sources tool
- "Search for X" → Use search_documents tool
- "Find code examples" → Use search_code_examples tool

**Response Guidelines:**
- Provide direct answers based on retrieved content
- Include relevant quotes
- Cite sources with URLs
- Admit when information is not found"""
```

## Structured Output

### Output Schema Design

**Agent outputs use Pydantic BaseModel for LLM-generated structured data.**

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class AnalysisOutput(BaseModel):
    """
    Structured output from analysis agent.
    
    Pydantic validates LLM-generated output at runtime.
    """
    # Required fields
    summary: str = Field(
        description="Comprehensive summary of analysis",
        min_length=100,  # Validation rule
    )
    
    # Constrained types
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall sentiment classification"
    )
    
    # Numeric constraints
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )
    
    # Lists with descriptions
    key_points: List[str] = Field(
        description="List of key points (3-5 items)",
        min_items=3,
        max_items=5,
    )
    
    # Nested structures
    metadata: dict[str, str] = Field(
        description="Additional metadata as key-value pairs"
    )
```

### Multiple Output Types (Union)

Agents can return different structured outputs:

```python
from pydantic import BaseModel

class SuccessResult(BaseModel):
    data: dict
    message: str

class FailureResult(BaseModel):
    error: str
    retry_suggested: bool

# Agent with multiple output types
agent = Agent(
    'openai:gpt-4o',
    output_type=[SuccessResult, FailureResult],
)
```

### Output Validation and Retries

Pydantic-AI automatically retries if output validation fails:

```python
class StrictOutput(BaseModel):
    score: int = Field(ge=0, le=100)  # Must be 0-100
    category: Literal["A", "B", "C"]  # Must be one of three

# If LLM returns score=150, Pydantic validation fails
# Agent automatically retries with error message to LLM
```

## Complete Agent Examples

### Example 1: Simple Query Agent

```python
"""Simple agent for answering questions about a knowledge base."""

from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

@dataclass
class QueryDependencies:
    knowledge_base: dict[str, str]

class QueryResult(BaseModel):
    answer: str = Field(description="Answer to the question")
    sources: list[str] = Field(description="Sources used")
    confidence: float = Field(ge=0.0, le=1.0)

agent = Agent(
    'openai:gpt-4o',
    deps_type=QueryDependencies,
    result_type=QueryResult,
    system_prompt="Answer questions using the provided knowledge base.",
)

@agent.tool
async def search_knowledge_base(
    ctx: RunContext[QueryDependencies],
    query: str
) -> str:
    """Search the knowledge base for relevant information."""
    kb = ctx.deps.knowledge_base
    # Simple keyword search
    results = [v for k, v in kb.items() if query.lower() in k.lower()]
    return "\n".join(results) if results else "No results found."

# Usage
async def main():
    deps = QueryDependencies(
        knowledge_base={
            "python": "Python is a programming language.",
            "ai": "AI stands for Artificial Intelligence.",
        }
    )
    result = await agent.run("What is Python?", deps=deps)
    print(result.answer)
```

### Example 2: Multi-Step Workflow Agent (from Archon)

```python
"""Document agent with multi-step operations."""

import logging
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base_agent import AgentDependencies, BaseAgent

logger = logging.getLogger(__name__)

@dataclass
class DocumentDependencies(AgentDependencies):
    project_id: str
    user_id: str | None = None
    progress_callback: Any | None = None

class DocumentOperation(BaseModel):
    """Result of document operation."""
    operation_type: str = Field(description="Type of operation performed")
    document_id: str = Field(description="ID of affected document")
    success: bool
    message: str

class DocumentAgent(BaseAgent[DocumentDependencies, DocumentOperation]):
    """Agent for document management operations."""
    
    def _create_agent(self, **kwargs) -> Agent:
        agent = Agent(
            model=self.model,
            deps_type=DocumentDependencies,
            result_type=DocumentOperation,
            system_prompt="""You are a Document Management Assistant.

**Capabilities:**
- Create new documents (PRDs, specs, notes)
- Update existing documents
- Query document information

**Approach:**
1. Listen to user's document needs
2. Use appropriate tools
3. Provide clear feedback
4. Confirm before destructive changes""",
            **kwargs,
        )
        
        @agent.system_prompt
        async def add_project_context(ctx: RunContext[DocumentDependencies]) -> str:
            return f"""
**Current Context:**
- Project ID: {ctx.deps.project_id}
- User ID: {ctx.deps.user_id or "Unknown"}
- Timestamp: {datetime.now().isoformat()}
"""
        
        @agent.tool
        async def create_document(
            ctx: RunContext[DocumentDependencies],
            title: str,
            document_type: str,
            content_description: str,
        ) -> str:
            """Create a new document."""
            try:
                # Progress update
                if ctx.deps.progress_callback:
                    await ctx.deps.progress_callback({
                        "step": "creating",
                        "title": title,
                    })
                
                # Generate document structure
                blocks = self._generate_blocks(title, document_type, content_description)
                
                # Create document
                doc_id = await document_service.create(
                    project_id=ctx.deps.project_id,
                    title=title,
                    blocks=blocks,
                )
                
                return f"Created document '{title}' (ID: {doc_id})"
            except Exception as e:
                logger.error(f"Error creating document: {e}")
                return f"Error: {str(e)}"
        
        @agent.tool
        async def list_documents(ctx: RunContext[DocumentDependencies]) -> str:
            """List all documents in the project."""
            try:
                docs = await document_service.list(ctx.deps.project_id)
                return "\n".join([f"- {doc['title']} ({doc['type']})" for doc in docs])
            except Exception as e:
                return f"Error: {str(e)}"
        
        return agent
    
    def get_system_prompt(self) -> str:
        return "Document management system prompt..."
    
    def _generate_blocks(self, title, doc_type, description):
        """Helper to generate document blocks."""
        # Implementation...
        return []
```

### Example 3: Streaming Agent

```python
"""Agent with streaming output support."""

async def stream_analysis():
    """Stream analysis results in real-time."""
    agent = VideoAnalysisAgent()
    
    deps = VideoAnalysisDependencies(
        video_id="example123",
        api_key="...",
    )
    
    # Use run_stream for streaming
    async with agent.run_stream("Analyze this video", deps=deps) as result:
        # Stream partial results
        async for partial in result.stream_text():
            print(partial, end="", flush=True)
        
        # Get final structured output
        final_result = await result.get_output()
        print(f"\n\nFinal: {final_result}")
```

## Testing Agents

### Unit Testing Agent Tools

```python
"""Test individual agent tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_search_documents_tool():
    """Test search_documents tool."""
    # Mock dependencies
    mock_client = AsyncMock()
    mock_client.perform_rag_query.return_value = {
        "success": True,
        "matches": [{"content": "Result 1"}],
    }
    
    # Create dependencies
    deps = RagDependencies(
        project_id="test",
        match_count=5,
    )
    
    # Mock RunContext
    ctx = MagicMock()
    ctx.deps = deps
    
    # Test tool (call function directly)
    with patch('agents.rag_agent.get_mcp_client', return_value=mock_client):
        result = await search_documents(ctx, query="test query")
    
    # Assertions
    assert "Result 1" in result
    mock_client.perform_rag_query.assert_called_once()
```

### Integration Testing Agents

```python
"""Test complete agent workflows."""

@pytest.mark.asyncio
async def test_document_creation_workflow():
    """Test end-to-end document creation."""
    # Create agent
    agent = DocumentAgent(model="openai:gpt-4o")
    
    # Create dependencies with test database
    deps = DocumentDependencies(
        project_id="test-project",
        user_id="test-user",
    )
    
    # Run agent
    result = await agent.run(
        "Create a PRD for user authentication",
        deps=deps
    )
    
    # Assertions
    assert result.success
    assert result.operation_type == "create"
    assert "authentication" in result.message.lower()
```

### Mocking LLM Responses

```python
"""Mock LLM for deterministic testing."""

from pydantic_ai.models.test import TestModel

def test_agent_with_mock_llm():
    """Test agent logic without calling real LLM."""
    # Create test model (returns predefined responses)
    test_model = TestModel()
    
    agent = Agent(
        test_model,
        deps_type=MyDependencies,
        result_type=MyOutput,
    )
    
    # Run with mock
    result = agent.run_sync("test prompt", deps=my_deps)
    
    # Test model records all calls
    assert len(test_model.last_model_request_parameters.messages) > 0
```

## Best Practices

### 1. Agent Scope and Responsibility

**DO:**
- ✅ Create specialized agents for specific domains (documents, search, analysis)
- ✅ Agents orchestrate tools and reasoning
- ✅ Clear, focused system prompts

**DON'T:**
- ❌ Create one mega-agent that does everything
- ❌ Put business logic in agents (belongs in tools/services)
- ❌ Duplicate tool functionality in multiple agents

### 2. Dependency Management

**DO:**
- ✅ Use dataclasses for dependencies
- ✅ Inject all external resources (DB, APIs, clients)
- ✅ Provide optional callbacks for progress updates
- ✅ Use type hints for all dependencies

**DON'T:**
- ❌ Access globals or singletons inside tools
- ❌ Create dependencies inside tools
- ❌ Hide required dependencies (make them explicit)

### 3. Tool Design

**DO:**
- ✅ One tool = one clear action
- ✅ Descriptive docstrings (LLM sees these)
- ✅ Return strings or JSON-serializable data
- ✅ Handle errors gracefully

**DON'T:**
- ❌ Tools that do multiple unrelated things
- ❌ Tools with side effects (without clear docstring warning)
- ❌ Return complex objects (use JSON/strings)

### 4. System Prompts

**DO:**
- ✅ Clear role and capabilities
- ✅ Step-by-step approach
- ✅ Examples of common queries
- ✅ Dynamic prompts for context (`@agent.system_prompt`)

**DON'T:**
- ❌ Vague or generic prompts
- ❌ Overly long prompts (use dynamic prompts for details)
- ❌ Forget to update prompts when adding tools

### 5. Structured Output

**DO:**
- ✅ Use Pydantic BaseModel for agent outputs
- ✅ Add Field descriptions for LLM guidance
- ✅ Use validation rules (ge, le, min_length, etc.)
- ✅ Provide clear field descriptions

**DON'T:**
- ❌ Use plain dicts for structured output
- ❌ Missing validation rules (LLM will make mistakes)
- ❌ Vague field names

### 6. Error Handling

**DO:**
- ✅ Try/except in all tools
- ✅ Return error messages (not raise exceptions)
- ✅ Log errors for debugging
- ✅ Use rate limiting for LLM APIs

**DON'T:**
- ❌ Let exceptions propagate to LLM
- ❌ Generic error messages
- ❌ Ignore retry logic

### 7. Testing

**DO:**
- ✅ Unit test individual tools
- ✅ Mock external dependencies
- ✅ Integration tests for workflows
- ✅ Use TestModel for deterministic tests

**DON'T:**
- ❌ Test agents only end-to-end
- ❌ Rely on real LLM calls in tests
- ❌ Skip edge cases and error scenarios

## Checklist for New Agents

Before committing a new agent:

- [ ] Agent inherits from `BaseAgent`
- [ ] Dependencies defined as dataclass extending `AgentDependencies`
- [ ] Output defined as Pydantic `BaseModel` (not dataclass)
- [ ] All tools have type hints and docstrings
- [ ] System prompt is clear and comprehensive
- [ ] Tools access dependencies via `ctx.deps`
- [ ] Error handling in all tools
- [ ] Progress callbacks implemented (if needed)
- [ ] Unit tests for tools
- [ ] Integration test for agent workflow
- [ ] Documentation updated

## Additional Resources

- **Pydantic-AI Official Docs**: https://ai.pydantic.dev/
- **Archon Framework Reference**: https://github.com/coleam00/Archon
- **MCP CE Agent Examples**: `src/mcp_ce/agents/`
- **Base Agent Implementation**: `src/mcp_ce/agents/base_agent.py`

## Examples in This Project

**Existing Agent Implementations:**
- `src/mcp_ce/agents/sample/sample_agent.py` - Simple triage assistant
- Future: YouTube analysis agent, document management agent, etc.

**Tool Reference:**
- `src/mcp_ce/tools/` - Atomic tools (not agents)
- Note distinction: Tools are deterministic, agents use LLM reasoning
