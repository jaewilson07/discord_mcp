# Agent Model Configuration

All agents now support dynamic LLM model selection via environment variables.

## Environment Variables

Add these to your `.env` file to configure which models each agent uses:

```bash
# Agent-specific models (optional)
SCRAPER_AGENT_MODEL=openai:gpt-4o-mini
EXTRACTION_AGENT_MODEL=openai:gpt-4o
VALIDATION_AGENT_MODEL=openai:gpt-4o-mini
WORKFLOW_AGENT_MODEL=openai:gpt-4o

# Default model for all agents (if specific not set)
DEFAULT_AGENT_MODEL=openai:gpt-4o

# Note: If no env vars are set, defaults to "openai:gpt-4o"
```

## How It Works

1. **Agent-specific**: Each agent checks for its own env var first (e.g., `SCRAPER_AGENT_MODEL`)
2. **Default fallback**: If not set, uses `DEFAULT_AGENT_MODEL`
3. **Hardcoded fallback**: If neither set, uses `"openai:gpt-4o"`

## Supported Model Formats

Models should be in format: `provider:model-name`

Examples:
- `openai:gpt-4o`
- `openai:gpt-4o-mini`
- `anthropic:claude-3-5-sonnet-20241022`
- `groq:llama-3.3-70b-versatile`

## Cost Optimization Example

```bash
# Use cheaper models for simple tasks
SCRAPER_AGENT_MODEL=openai:gpt-4o-mini      # Simple coordination
VALIDATION_AGENT_MODEL=openai:gpt-4o-mini   # Simple checking

# Use powerful models for complex tasks
EXTRACTION_AGENT_MODEL=openai:gpt-4o        # Complex extraction
WORKFLOW_AGENT_MODEL=openai:gpt-4o          # Orchestration
```

## Implementation

- Base agents: Use `_get_model()` helper from `_model_helper.py`
- Workflow agent: Uses inline `_get_workflow_model()` helper
- Pattern matches MCP tools' model configuration approach
