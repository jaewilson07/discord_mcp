# Event Extraction Agent - Implementation Plan

## Overview

Build a Pydantic-AI agent that extracts multiple events from a URL with self-verification and iterative refinement until confident all events are found.

## Problem Statement

Current `create_from_url.py` is a function-based workflow, not an agent. It:
- ❌ Extracts only ONE event per URL
- ❌ No self-verification loop
- ❌ No confidence scoring for completeness
- ❌ Not conversational/interactive

**Goal:** Create an agent that can:
- ✅ Extract MULTIPLE events from a single URL
- ✅ Loop over itself until confident all events found
- ✅ Provide confidence scores per event
- ✅ Use Pydantic-AI patterns (tools, deps, structured output)

## Architecture

### Agent Pattern: EventExtractionAgent

Following Pydantic-AI patterns from `.github/instructions/pydantic-ai-agents.instructions.md`:

```python
EventExtractionAgent(BaseAgent[EventDependencies, EventExtractionResult])
    ├── Dependencies (dataclass)
    │   ├── url: str
    │   ├── scraped_content: str
    │   ├── max_iterations: int = 5
    │   ├── confidence_threshold: float = 0.85
    │   └── progress_callback: Optional[Callable] = None
    │
    ├── Output (Pydantic BaseModel)
    │   ├── events: List[EventDetails]
    │   ├── overall_confidence: float
    │   ├── iterations_used: int
    │   └── extraction_complete: bool
    │
    └── Tools
        ├── search_for_event_patterns() - Find event indicators
        ├── extract_single_event() - Extract one event
        ├── verify_event_completeness() - Check if found all events
        └── assess_confidence() - Score extraction quality
```

### Self-Verification Loop

The agent uses **iterative refinement** inspired by Pydantic-AI's retry mechanism:

```
1. Initial Extraction → Extract N events
2. Confidence Check → Score each event + overall
3. If confidence < threshold:
   - Re-analyze content
   - Look for missed patterns
   - Extract additional events
   - Go to step 2
4. Return final result
```

## Data Models

### Dependencies (Dataclass)

```python
@dataclass
class EventExtractionDependencies(AgentDependencies):
    """Dependencies for event extraction operations."""
    url: str
    scraped_content: str
    max_iterations: int = 5
    confidence_threshold: float = 0.85
    progress_callback: Optional[Callable] = None
    discord_server_id: Optional[str] = None
    save_to_notion: bool = True
    notion_database_id: Optional[str] = None
```

### Output (Pydantic BaseModel)

```python
class EventExtractionResult(BaseModel):
    """LLM-generated extraction result with validation."""
    events: List[EventDetails] = Field(description="All extracted events")
    overall_confidence: float = Field(
        ge=0.0, le=1.0, 
        description="Confidence all events found"
    )
    iterations_used: int = Field(description="Number of iterations performed")
    extraction_complete: bool = Field(description="Whether extraction is complete")
    missed_indicators: List[str] = Field(
        default_factory=list,
        description="Potential event indicators that weren't extracted"
    )
```

## Implementation Steps

### Phase 1: Agent Structure (File: `event_extraction_agent.py`)

**Task 1:** Create base agent class
```python
class EventExtractionAgent(BaseAgent[EventExtractionDependencies, EventExtractionResult]):
    """
    Agent for extracting multiple events from URLs with self-verification.
    
    Capabilities:
    - Extract multiple events from single URL
    - Iterative refinement with confidence scoring
    - Self-verification loop
    - Quality assessment per event
    """
    
    def __init__(self, model: str = "openai:gpt-4o", **kwargs):
        super().__init__(
            model=model,
            name="EventExtractionAgent",
            **kwargs,
        )
    
    def _create_agent(self, **kwargs) -> Agent:
        # Implementation
        pass
    
    def get_system_prompt(self) -> str:
        # Implementation
        pass
```

### Phase 2: Agent Tools

**Tool 1: search_for_event_patterns**
```python
@agent.tool
async def search_for_event_patterns(
    ctx: RunContext[EventExtractionDependencies]
) -> str:
    """
    Search scraped content for event indicators.
    
    Looks for:
    - Date patterns (Nov 23, 2025, etc.)
    - Time patterns (7:00 PM, 19:00, etc.)
    - Event keywords (concert, workshop, class, performance)
    - Location indicators (venue, address, online)
    
    Returns: Summary of found patterns with counts
    """
```

**Tool 2: extract_single_event**
```python
@agent.tool
async def extract_single_event(
    ctx: RunContext[EventExtractionDependencies],
    event_section: str,
    event_index: int
) -> EventDetails:
    """
    Extract a single event from a content section.
    
    Args:
        event_section: The text containing event information
        event_index: Which event this is (for tracking)
        
    Returns: EventDetails object with extracted information
    """
```

**Tool 3: verify_event_completeness**
```python
@agent.tool
async def verify_event_completeness(
    ctx: RunContext[EventExtractionDependencies],
    extracted_events: List[EventDetails]
) -> dict:
    """
    Verify if all events have been extracted.
    
    Checks:
    - Number of date patterns vs events found
    - Unmatched event keywords
    - Content sections not covered
    - Confidence scoring
    
    Returns: Dict with completeness score and missing indicators
    """
```

**Tool 4: assess_event_quality**
```python
@agent.tool
async def assess_event_quality(
    ctx: RunContext[EventExtractionDependencies],
    event: EventDetails
) -> dict:
    """
    Assess quality/completeness of a single event.
    
    Scores:
    - Date/time completeness
    - Location information
    - Description quality
    - Organizer information
    
    Returns: Dict with quality scores
    """
```

### Phase 3: System Prompt

```python
def get_system_prompt(self) -> str:
    return """You are an Event Extraction Expert specializing in finding ALL events on web pages.

Your Capabilities:
- Extract multiple events from single web pages
- Identify event patterns (dates, times, venues)
- Assess extraction completeness
- Iteratively refine until confident all events found

Your Approach:
1. **Initial Scan** - Use search_for_event_patterns to find all event indicators
2. **Extract Each Event** - Use extract_single_event for each found event
3. **Quality Check** - Use assess_event_quality for each event
4. **Completeness Verification** - Use verify_event_completeness
5. **Iterate if Needed** - If confidence < threshold, re-scan for missed events

Important Rules:
- ALWAYS look for multiple events (don't stop at first one)
- Use date/time patterns to count expected events
- Match event count to pattern count
- Report confidence honestly
- Flag potentially missed events

Common Event Patterns:
- Event calendars (multiple dates listed)
- Recurring events (weekly, monthly)
- Series (Part 1, Part 2, Session A, Session B)
- Multi-day events
- Different venues/locations

Output Requirements:
- Return ALL found events in events list
- Set extraction_complete=True only if confident
- Provide overall_confidence score
- List any missed_indicators
"""
```

### Phase 4: Self-Verification Loop

Implement in `run()` method override:

```python
async def run(self, user_prompt: str, deps: EventExtractionDependencies) -> EventExtractionResult:
    """
    Run agent with self-verification loop.
    
    Iterates until:
    - Confidence >= threshold
    - Max iterations reached
    - No new events found
    """
    iteration = 0
    all_events = []
    
    while iteration < deps.max_iterations:
        iteration += 1
        
        # Progress callback
        if deps.progress_callback:
            await deps.progress_callback({
                "iteration": iteration,
                "events_found": len(all_events),
            })
        
        # Run agent
        result = await super().run(user_prompt, deps)
        
        # Check completeness
        if result.extraction_complete:
            break
        
        if result.overall_confidence >= deps.confidence_threshold:
            break
        
        # Update prompt with previous results
        user_prompt = f"""Previous iteration found {len(result.events)} events.
Confidence: {result.overall_confidence:.2f}
Missed indicators: {result.missed_indicators}

Please re-analyze and find any remaining events."""
    
    return result
```

### Phase 5: Integration with Existing Workflow

Create wrapper function that uses agent:

```python
async def extract_events_from_url(
    url: str,
    discord_server_id: Optional[str] = None,
    save_to_notion: bool = True,
    notion_database_id: Optional[str] = None,
    max_iterations: int = 5,
    confidence_threshold: float = 0.85,
) -> Dict[str, Any]:
    """
    Extract all events from URL using EventExtractionAgent.
    
    Workflow:
    1. Scrape URL (existing crawl_website tool)
    2. Run EventExtractionAgent with self-verification loop
    3. Create Discord events for each extracted event
    4. Save each event to Notion (if enabled)
    
    Returns:
    - events: List[EventDetails]
    - discord_event_urls: List[str]
    - notion_page_ids: List[str]
    - overall_confidence: float
    - success: bool
    """
```

## Testing Strategy

### Unit Tests

**File:** `TESTS/mcp_ce/agents/events/test_event_extraction_agent.py`

```python
@pytest.mark.asyncio
async def test_extract_multiple_events():
    """Test agent extracts multiple events from calendar page."""
    agent = EventExtractionAgent()
    deps = EventExtractionDependencies(
        url="https://example.com/events",
        scraped_content=sample_calendar_content,
        max_iterations=3,
        confidence_threshold=0.8,
    )
    
    result = await agent.run("Extract all events", deps=deps)
    
    assert len(result.events) >= 2
    assert result.overall_confidence >= 0.8
    assert result.extraction_complete

@pytest.mark.asyncio
async def test_self_verification_loop():
    """Test agent iterates until confident."""
    agent = EventExtractionAgent()
    # Use content with subtle/hidden events
    result = await agent.run("Extract all events", deps=deps)
    
    assert result.iterations_used > 1
    assert result.overall_confidence >= deps.confidence_threshold
```

### Integration Test

**File:** `TEMP/test_event_agent_live.py`

```python
async def test_live_extraction():
    """Test on real Seattle Blues Dance URL."""
    result = await extract_events_from_url(
        url="https://seattlebluesdance.com/",
        save_to_notion=False,  # Test only
    )
    
    print(f"Events found: {len(result['events'])}")
    for event in result['events']:
        print(f"  - {event.title} ({event.date})")
    
    assert result['success']
    assert len(result['events']) > 0
    assert result['overall_confidence'] >= 0.7
```

## Success Criteria

- ✅ Agent extracts **multiple events** from single URL
- ✅ Self-verification loop runs until confidence threshold met
- ✅ Confidence scoring per event and overall
- ✅ Integration with existing Discord/Notion workflow
- ✅ Test suite validates multi-event extraction
- ✅ Works on real-world URLs (seattlebluesdance.com)

## File Structure

```
src/mcp_ce/agents/events/
├── event_extraction_agent.py       # Main agent (NEW)
├── create_from_url.py              # Legacy (keep for reference)
├── extract_events_workflow.py      # Wrapper using agent (NEW)
└── IMPLEMENTATION_PLAN.md          # This file

TESTS/mcp_ce/agents/events/
└── test_event_extraction_agent.py  # Test suite (NEW)

TEMP/
└── test_event_agent_live.py        # Live testing (NEW)
```

## Next Steps

1. ✅ Create implementation plan (this document)
2. ⏭️ Implement EventExtractionAgent base structure
3. ⏭️ Add agent tools (search, extract, verify, assess)
4. ⏭️ Implement self-verification loop
5. ⏭️ Create wrapper function with Discord/Notion integration
6. ⏭️ Write test suite
7. ⏭️ Test on seattlebluesdance.com
8. ⏭️ Refactor create_from_url to use agent

## Notes

- Uses Pydantic-AI patterns (BaseAgent, tools, structured output)
- Self-verification inspired by Pydantic's retry mechanism
- Maintains backward compatibility with existing EventDetails model
- Integrates with existing Discord/Notion tools
- Follows atomic tool design (tools don't call other tools directly)
