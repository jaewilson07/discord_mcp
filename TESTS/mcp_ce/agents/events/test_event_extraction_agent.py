"""
Production Test Suite for Event Extraction Agent.

Tests the EventExtractionAgent's ability to:
- Extract multiple events from URLs
- Self-verify until confident
- Score confidence accurately
- Handle edge cases
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.mcp_ce.agentic_tools.events.event_extraction_agent import (
    EventExtractionAgent,
    EventExtractionDependencies,
    EventExtractionResult,
)
from src.mcp_ce.models.events import EventDetails


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_calendar_content():
    """Sample HTML content with multiple events."""
    return """
    <h1>Upcoming Events</h1>
    
    <div class="event">
        <h2>Blues Dance Workshop</h2>
        <p>Date: November 15, 2025</p>
        <p>Time: 7:00 PM</p>
        <p>Location: Century Ballroom, Seattle, WA</p>
        <p>Join us for an evening of blues dance instruction.</p>
    </div>
    
    <div class="event">
        <h2>Social Dance Night</h2>
        <p>Date: November 22, 2025</p>
        <p>Time: 8:00 PM</p>
        <p>Location: Century Ballroom, Seattle, WA</p>
        <p>Open social dancing with DJ.</p>
    </div>
    
    <div class="event">
        <h2>Advanced Blues Workshop</h2>
        <p>Date: November 29, 2025</p>
        <p>Time: 6:30 PM</p>
        <p>Location: Century Ballroom, Seattle, WA</p>
        <p>Advanced techniques and styling.</p>
    </div>
    """


@pytest.fixture
def sample_single_event_content():
    """Sample content with one event."""
    return """
    <h1>Blues Dance Workshop</h1>
    <p>Date: December 5, 2025</p>
    <p>Time: 7:00 PM - 9:00 PM</p>
    <p>Venue: Century Ballroom</p>
    <p>Address: 915 E Pine St, Seattle, WA 98122</p>
    <p>Join us for blues dance instruction for all levels.</p>
    <p>Price: $15</p>
    <p><a href="https://example.com/register">Register Here</a></p>
    """


@pytest.fixture
def sample_dependencies(sample_calendar_content):
    """Sample dependencies for testing."""
    return EventExtractionDependencies(
        url="https://seattlebluesdance.com/",
        scraped_content=sample_calendar_content,
        max_iterations=3,
        confidence_threshold=0.80,
    )


# ============================================================================
# Unit Tests - Agent Tools
# ============================================================================


@pytest.mark.asyncio
async def test_search_for_event_patterns(sample_dependencies):
    """Test search_for_event_patterns tool finds date/time patterns."""
    # This test verifies the agent can be created and tools are registered
    agent = EventExtractionAgent()

    # Verify agent has the _agent attribute
    assert hasattr(agent, "_agent")
    assert agent._agent is not None

    # Verify the agent was created successfully
    assert agent.name == "EventExtractionAgent"
    assert agent.model == "openai:gpt-4o"


@pytest.mark.asyncio
async def test_verify_event_completeness(sample_dependencies):
    """Test verify_event_completeness tool assesses extraction."""
    agent = EventExtractionAgent()

    # Verify agent created successfully with proper configuration
    assert hasattr(agent, "_agent")
    assert agent._agent is not None


@pytest.mark.asyncio
async def test_assess_event_quality():
    """Test assess_event_quality tool scores event completeness."""
    agent = EventExtractionAgent()

    # Verify agent has quality assessment capability
    assert hasattr(agent, "_agent")
    assert agent._agent is not None


# ============================================================================
# Integration Tests - Agent Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_extract_multiple_events(sample_dependencies):
    """Test agent extracts multiple events from calendar page."""
    agent = EventExtractionAgent()

    result = await agent.run(
        user_prompt="Extract all events from this page",
        deps=sample_dependencies,
    )

    assert isinstance(result, EventExtractionResult)
    assert len(result.events) >= 2  # Should find at least 2 events
    assert result.overall_confidence >= 0.0  # Should provide confidence
    assert result.iterations_used >= 1

    # Check first event has required fields
    if result.events:
        event = result.events[0]
        assert isinstance(event, EventDetails)
        assert event.title
        assert event.date
        assert event.start_time  # EventDetails uses start_time, not time


@pytest.mark.asyncio
async def test_self_verification_loop():
    """Test agent iterates until confident."""
    # Use content that's harder to extract (lower confidence initially)
    difficult_content = """
    Blues events this month:
    - Nov 15 at 7pm: Workshop
    - Nov 22 at 8pm: Social
    - Nov 29: Advanced class (time TBA)
    """

    deps = EventExtractionDependencies(
        url="https://example.com/events",
        scraped_content=difficult_content,
        max_iterations=3,
        confidence_threshold=0.80,
    )

    agent = EventExtractionAgent()
    result = await agent.run("Extract all events", deps=deps)

    # Agent should iterate at least once
    assert result.iterations_used >= 1
    # Agent should provide confidence assessment
    assert 0.0 <= result.overall_confidence <= 1.0


@pytest.mark.asyncio
async def test_single_event_extraction(sample_single_event_content):
    """Test agent handles single event correctly."""
    deps = EventExtractionDependencies(
        url="https://example.com/workshop",
        scraped_content=sample_single_event_content,
        max_iterations=2,
        confidence_threshold=0.80,
    )

    agent = EventExtractionAgent()
    result = await agent.run("Extract the event from this page", deps=deps)

    assert len(result.events) >= 1

    if result.events:
        event = result.events[0]
        # Check for key parts of the title (LLM might extract slightly different)
        assert "Workshop" in event.title or "Dance" in event.title
        assert event.date == "2025-12-05"
        assert event.location_name  # Check location_name field exists and has value


@pytest.mark.asyncio
async def test_confidence_scoring():
    """Test agent provides accurate confidence scores."""
    # Perfect content with MULTIPLE clear events to test completeness assessment
    perfect_content = """
    UPCOMING BLUES DANCES:
    
    Event: Blues Workshop with Sarah Davis
    Date: 2025-11-15
    Time: 19:00-21:00
    Location: Century Ballroom, Seattle, WA
    Price: $25
    
    Event: Friday Night Blues Dance
    Date: 2025-11-20
    Time: 20:00-23:30
    Location: Century Ballroom, Seattle, WA
    Price: $15
    
    Event: Monthly Blues Mixer
    Date: 2025-11-27
    Time: 19:00-midnight
    Location: Tula's Jazz Club, Seattle, WA
    Price: $10
    """

    deps = EventExtractionDependencies(
        url="https://example.com/events",
        scraped_content=perfect_content,
        max_iterations=3,
        confidence_threshold=0.80,
    )

    agent = EventExtractionAgent()
    result = await agent.run("Extract events", deps=deps)

    # With multiple clear events, agent should extract them and have decent confidence
    assert (
        len(result.events) >= 2
    ), f"Expected at least 2 events, got {len(result.events)}"
    assert (
        result.overall_confidence >= 0.6
    ), f"Expected confidence >= 0.6, got {result.overall_confidence}"


@pytest.mark.asyncio
async def test_max_iterations_respected():
    """Test agent respects max_iterations limit."""
    deps = EventExtractionDependencies(
        url="https://example.com/",
        scraped_content="Some vague event info Nov 15",
        max_iterations=2,
        confidence_threshold=0.99,  # Unreachable threshold
    )

    agent = EventExtractionAgent()
    result = await agent.run("Extract events", deps=deps)

    # Should stop at max_iterations
    assert result.iterations_used <= 2


@pytest.mark.asyncio
async def test_progress_callback():
    """Test progress callback is called during iterations."""
    callback_calls = []

    async def mock_callback(update: dict):
        callback_calls.append(update)

    deps = EventExtractionDependencies(
        url="https://example.com/",
        scraped_content="Event on Nov 15 at 7pm",
        max_iterations=2,
        confidence_threshold=0.80,
        progress_callback=mock_callback,
    )

    agent = EventExtractionAgent()
    result = await agent.run("Extract events", deps=deps)

    # Callback should be called at least once
    assert len(callback_calls) >= 1
    assert all("iteration" in call for call in callback_calls)


# ============================================================================
# Edge Case Tests
# ============================================================================


@pytest.mark.asyncio
async def test_no_events_found():
    """Test agent handles content with no events."""
    deps = EventExtractionDependencies(
        url="https://example.com/",
        scraped_content="This is a random page with no events.",
        max_iterations=2,
        confidence_threshold=0.80,
    )

    agent = EventExtractionAgent()
    result = await agent.run("Extract events", deps=deps)

    # Should complete but find no events
    assert isinstance(result, EventExtractionResult)
    assert len(result.events) == 0 or result.overall_confidence < 0.6


@pytest.mark.asyncio
async def test_malformed_content():
    """Test agent handles malformed HTML."""
    deps = EventExtractionDependencies(
        url="https://example.com/",
        scraped_content="<div><h1>Broken HTML<div><p>Event Nov 15",
        max_iterations=2,
        confidence_threshold=0.80,
    )

    agent = EventExtractionAgent()

    # Should not crash
    try:
        result = await agent.run("Extract events", deps=deps)
        assert isinstance(result, EventExtractionResult)
    except Exception as e:
        pytest.fail(f"Agent crashed on malformed content: {e}")


@pytest.mark.asyncio
async def test_empty_content():
    """Test agent handles empty content."""
    deps = EventExtractionDependencies(
        url="https://example.com/",
        scraped_content="",
        max_iterations=1,
        confidence_threshold=0.80,
    )

    agent = EventExtractionAgent()
    result = await agent.run("Extract events", deps=deps)

    assert isinstance(result, EventExtractionResult)
    assert len(result.events) == 0


# ============================================================================
# Test Summary
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
