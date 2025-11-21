// Event Extraction Agent Graph

Multi-agent workflow for extracting events from web pages, following Pydantic-AI best practices.

## Architecture Overview

This implementation follows the **agent delegation pattern** from Pydantic-AI's flight booking example, where specialized agents work together to complete a complex task.

### Agent Graph Flow

```
START
  ↓
workflow_agent (orchestrator)
  ↓
scraper_agent → ScrapedContent
  ↓
extraction_agent → ExtractionResult
  ↓
validation_agent → ValidationResult
  ↓
[Retry if needed] → extraction_agent
  ↓
EventExtractionWorkflowResult
  ↓
END
```

### Specialized Agents

1. **Scraper Agent** (`scraper_agent`)
   - Responsibility: Web scraping using Crawl4AI
   - Output: `ScrapedContent | ScrapingFailed`
   - Tools: `scrape_url()`

2. **Extraction Agent** (`extraction_agent`)
   - Responsibility: Extract all events from scraped content
   - Output: `ExtractionResult`
   - Tools: `search_for_patterns()`, `get_content_section()`

3. **Validation Agent** (`validation_agent`)
   - Responsibility: Validate extraction completeness
   - Output: `ValidationResult`
   - Tools: `analyze_extraction_completeness()`, `check_event_quality()`

4. **Workflow Agent** (`workflow_agent`)
   - Responsibility: Orchestrate the entire workflow
   - Output: `EventExtractionWorkflowResult`
   - Tools: `run_scraper()`, `run_extraction()`, `run_validation()`

## Project Structure

```
event_extraction_graph/
├── __init__.py              # Public API exports
├── agent.py                 # All 4 agents + main workflow
├── models.py                # Pydantic models for outputs
└── tools.py                 # Shared utility functions
```

### Following Best Practices

✅ **Pydantic Models for LLM Output** - All agent outputs use `BaseModel`  
✅ **Agent Delegation** - Workflow agent delegates to specialized agents  
✅ **Logfire Instrumentation** - All agents instrumented for observability  
✅ **Usage Tracking** - Shared `RunUsage` tracks all LLM calls  
✅ **Usage Limits** - Request limits prevent runaway costs  
✅ **Type Safety** - Full type hints throughout  

## Usage

### Simple Usage

```python
from mcp_ce.agents.event_extraction_graph import extract_events_from_url

result = await extract_events_from_url(
    url="https://seattlebluesdance.com/",
    max_iterations=2,
    confidence_threshold=0.85,
)

print(f"Found {len(result.events)} events")
for event in result.events:
    print(f"  - {event.title} on {event.date}")
```

### With Progress Callback

```python
def progress_update(status: dict):
    print(f"Progress: {status}")

result = await extract_events_from_url(
    url="https://example.com/events",
    progress_callback=progress_update,
)
```

## Data Models

### Input Models (Dependencies)

- `WorkflowDeps` - Main workflow configuration
- `ScraperDeps` - Scraper agent configuration
- `ExtractionDeps` - Extraction agent configuration
- `ValidationDeps` - Validation agent configuration

### Output Models (Pydantic BaseModel)

- `EventDetails` - Single event with all fields
- `ScrapedContent` - Scraping result
- `ExtractionResult` - Extraction result with events list
- `ValidationResult` - Validation assessment
- `EventExtractionWorkflowResult` - Final workflow output

### Error Models

- `ScrapingFailed` - Scraping error
- `ExtractionFailed` - Extraction error
- `NoEventsFound` - No events detected

## Tools

Shared utility functions in `tools.py`:

- `find_date_patterns()` - Regex pattern matching for dates
- `find_time_patterns()` - Regex pattern matching for times
- `find_event_keywords()` - Keyword detection
- `count_event_indicators()` - Count all indicators
- `validate_event_completeness()` - Check event quality
- `compare_extraction_iterations()` - Compare iterations
- `normalize_date()` - Normalize date formats
- `normalize_time()` - Normalize time formats

## Logfire Observability

All agents are instrumented with Pydantic Logfire:

```python
import logfire

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()
```

This provides:
- Request/response logging
- Token usage tracking
- Agent delegation visualization
- Error tracking
- Performance metrics

## Testing

Run the test script:

```bash
python TEMP/test_agent_graph.py
```

## Key Differences from Old Architecture

### Old (`event_extraction_agent.py`)
- ❌ Single monolithic agent
- ❌ All logic in one 622-line file
- ❌ Tools mixed with agent definition
- ❌ No agent delegation
- ❌ Basic logging only

### New (`event_extraction_graph/`)
- ✅ **4 specialized agents** (scraper, extraction, validation, workflow)
- ✅ **Modular structure** (agent.py, models.py, tools.py)
- ✅ **Agent delegation pattern** following Pydantic-AI examples
- ✅ **Logfire instrumentation** for observability
- ✅ **Clear separation of concerns**
- ✅ **Reusable tools** in separate module
- ✅ **Type-safe with Pydantic models**

## Integration with Discord/Notion

The workflow returns `EventExtractionWorkflowResult` which contains:
- `events: List[EventDetails]` - Ready for Discord/Notion export
- `overall_confidence` - Quality indicator
- `iterations_used` - Performance metric
- `extraction_complete` - Completeness flag

Each `EventDetails` has helper methods:
- `get_full_location()` - Formatted location string
- `convert_datetime_for_discord()` - ISO 8601 for Discord API

## Environment Setup

Required environment variables:
```
OPENAI_API_KEY=sk-...
LOGFIRE_TOKEN=... (optional, for Logfire integration)
```

## Performance

- **Max iterations**: 2 (configurable)
- **Usage limit**: 50 requests per workflow
- **Average time**: 30-60 seconds for typical pages
- **Token efficiency**: Shared usage tracking across all agents

## Future Enhancements

- [ ] Add Discord export agent
- [ ] Add Notion export agent  
- [ ] Support batch URL processing
- [ ] Add caching layer for repeated URLs
- [ ] Support streaming results
- [ ] Add evaluation suite with pydantic_evals
