"""
Agent tools for event extraction workflow.

These tools are used by the various agents in the graph.
Following Pydantic-AI patterns.
"""

import logging
from typing import Dict, Any, List
import re
from datetime import datetime

logger = logging.getLogger(__name__)


# ===== Pattern Recognition Tools =====


def find_date_patterns(content: str) -> List[str]:
    """
    Find date patterns in content.

    Returns list of matched date strings.
    """
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # MM/DD/YYYY or M/D/YY
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",  # Month DD, YYYY
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",  # DD Month YYYY
    ]

    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, content, re.IGNORECASE))

    return list(set(matches))  # Remove duplicates


def find_time_patterns(content: str) -> List[str]:
    """
    Find time patterns in content.

    Returns list of matched time strings.
    """
    patterns = [
        r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b",  # HH:MM AM/PM
        r"\b\d{1,2}\s*(?:AM|PM|am|pm)\b",  # H AM/PM
    ]

    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, content, re.IGNORECASE))

    return list(set(matches))


def find_event_keywords(content: str) -> List[str]:
    """
    Find event-related keywords in content.

    Returns list of found keywords.
    """
    keywords = [
        "workshop",
        "class",
        "dance",
        "party",
        "event",
        "show",
        "performance",
        "concert",
        "festival",
        "gathering",
        "meetup",
        "session",
        "lesson",
        "practice",
    ]

    found = []
    content_lower = content.lower()
    for keyword in keywords:
        if keyword in content_lower:
            found.append(keyword)

    return found


def count_event_indicators(content: str) -> Dict[str, int]:
    """
    Count various event indicators in content.

    Returns dict with counts for dates, times, keywords.
    """
    return {
        "dates": len(find_date_patterns(content)),
        "times": len(find_time_patterns(content)),
        "keywords": len(find_event_keywords(content)),
    }


# ===== Validation Tools =====


def validate_event_completeness(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that an event has all required and important fields.

    Returns validation result with scores and missing fields.
    """
    required_fields = ["title", "date", "start_time", "location_name"]
    important_fields = ["description", "organizer", "location_address"]
    optional_fields = ["registration_url", "price", "image_url", "end_time"]

    # Check required fields
    required_score = sum(
        1
        for field in required_fields
        if event_dict.get(field) and str(event_dict[field]).strip()
    ) / len(required_fields)

    # Check important fields
    important_score = sum(
        1
        for field in important_fields
        if event_dict.get(field) and str(event_dict[field]).strip()
    ) / len(important_fields)

    # Check optional fields
    optional_score = sum(
        1
        for field in optional_fields
        if event_dict.get(field) and str(event_dict[field]).strip()
    ) / len(optional_fields)

    # Overall quality (weighted)
    quality = required_score * 0.6 + important_score * 0.3 + optional_score * 0.1

    # Find missing fields
    missing_required = [
        field
        for field in required_fields
        if not event_dict.get(field) or not str(event_dict[field]).strip()
    ]

    missing_important = [
        field
        for field in important_fields
        if not event_dict.get(field) or not str(event_dict[field]).strip()
    ]

    return {
        "quality_score": quality,
        "required_score": required_score,
        "important_score": important_score,
        "optional_score": optional_score,
        "missing_required": missing_required,
        "missing_important": missing_important,
        "is_complete": required_score == 1.0,
    }


def compare_extraction_iterations(
    previous_events: List[Dict[str, Any]],
    current_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare two extraction iterations to see if improvements were made.

    Returns analysis of changes between iterations.
    """
    prev_count = len(previous_events)
    curr_count = len(current_events)

    # Calculate average quality for each iteration
    prev_quality = sum(
        validate_event_completeness(e)["quality_score"] for e in previous_events
    ) / max(prev_count, 1)

    curr_quality = sum(
        validate_event_completeness(e)["quality_score"] for e in current_events
    ) / max(curr_count, 1)

    return {
        "previous_count": prev_count,
        "current_count": curr_count,
        "count_change": curr_count - prev_count,
        "previous_quality": prev_quality,
        "current_quality": curr_quality,
        "quality_improvement": curr_quality - prev_quality,
        "improved": curr_count > prev_count or curr_quality > prev_quality,
    }


# ===== Date/Time Normalization =====


def normalize_date(date_str: str) -> str:
    """
    Normalize various date formats to YYYY-MM-DD.

    Returns normalized date string or original if parsing fails.
    """
    # Common date formats to try
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    logger.warning(f"Could not normalize date: {date_str}")
    return date_str


def normalize_time(time_str: str) -> str:
    """
    Normalize various time formats to HH:MM (24-hour).

    Returns normalized time string or original if parsing fails.
    """
    # Common time formats to try
    formats = [
        "%H:%M",
        "%I:%M %p",
        "%I:%M%p",
        "%I %p",
        "%I%p",
    ]

    time_str = time_str.strip()

    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            continue

    logger.warning(f"Could not normalize time: {time_str}")
    return time_str
