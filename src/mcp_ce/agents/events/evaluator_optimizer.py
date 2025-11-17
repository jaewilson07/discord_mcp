"""
Evaluator-Optimizer pattern for event extraction quality control.

This module implements the evaluator-optimizer pattern to ensure high-quality
event data extraction by iteratively evaluating and refining the extracted data.
"""

import asyncio
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel


class EventQualityScore(BaseModel):
    """Evaluation scores for extracted event data"""

    completeness: float  # 0-1: How complete is the data?
    accuracy: float  # 0-1: Does the data make sense?
    confidence: float  # 0-1: How confident are we?
    missing_fields: List[str]  # List of important missing fields
    issues: List[str]  # List of identified issues
    suggestions: List[str]  # List of improvement suggestions
    overall_score: float  # 0-1: Overall quality score
    should_deep_crawl: bool = False  # Should we crawl more pages?
    deep_crawl_reason: str = ""  # Why deep crawl is needed

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """Check if the quality is acceptable"""
        return self.overall_score >= threshold


async def evaluate_event_quality(
    event: "EventDetails", original_content: str
) -> EventQualityScore:
    """
    Evaluate the quality of extracted event details.

    Checks for:
    - Completeness: Are key fields populated?
    - Accuracy: Do dates/times make sense?
    - Confidence: Does the extracted data match the content?

    Args:
        event: Extracted EventDetails object
        original_content: Original scraped content (for verification)

    Returns:
        EventQualityScore with detailed evaluation
    """
    import os
    from openai import AsyncOpenAI
    import json

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    client = AsyncOpenAI(api_key=api_key)

    # Build evaluation prompt
    event_data = event.model_dump()

    prompt = f"""You are an expert event data quality evaluator. Analyze the extracted event data and score it.

EXTRACTED EVENT DATA:
{json.dumps(event_data, indent=2)}

ORIGINAL CONTENT (first 2000 chars):
{original_content[:2000]}

Evaluate the extraction on these criteria:

1. COMPLETENESS (0-1):
   - Are the critical fields (title, date, location) populated?
   - Are optional but valuable fields (time, description, organizer) present?
   - Score: 1.0 = all important fields present, 0.0 = missing critical fields

2. ACCURACY (0-1):
   - Does the date make sense (not in far past, reasonable format)?
   - If time is present, is it reasonable (business hours for most events)?
   - Does location match content?
   - Score: 1.0 = all data seems accurate, 0.0 = obvious errors

3. CONFIDENCE (0-1):
   - How well does the extracted data match the original content?
   - Are there contradictions or uncertainties?
   - Score: 1.0 = high confidence match, 0.0 = low confidence

4. DEEP CRAWL DECISION:
   - Should we crawl linked pages to get more information?
   - Consider: Is critical info missing? Does the page reference other pages (e.g., "Schedule", "Classes", "Lineup")?
   - If completeness < 0.6 OR missing critical fields, likely should deep crawl

Return a JSON object with:
{{
  "completeness": 0.0-1.0,
  "accuracy": 0.0-1.0,
  "confidence": 0.0-1.0,
  "missing_fields": ["field1", "field2"],  // Important missing fields
  "issues": ["issue1", "issue2"],  // Problems identified
  "suggestions": ["suggestion1", "suggestion2"],  // How to improve
  "overall_score": 0.0-1.0,  // Average of completeness, accuracy, confidence
  "should_deep_crawl": true/false,  // Should we crawl more pages?
  "deep_crawl_reason": "reason"  // Why or why not
}}

Return ONLY the JSON object."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert event data quality evaluator. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        result_text = response.choices[0].message.content

        # Extract JSON
        start_idx = result_text.find("{")
        end_idx = result_text.rfind("}") + 1

        if start_idx == -1 or end_idx <= start_idx:
            raise ValueError("No JSON found in response")

        json_text = result_text[start_idx:end_idx]
        data = json.loads(json_text)

        return EventQualityScore(**data)

    except Exception as e:
        # Fallback: Basic heuristic evaluation
        print(f"⚠️ AI evaluation failed, using heuristics: {e}")
        return _heuristic_evaluation(event)


def _heuristic_evaluation(event: "EventDetails") -> EventQualityScore:
    """Fallback heuristic-based evaluation"""
    completeness = 0.0
    missing_fields = []
    issues = []

    # Check critical fields
    if event.title:
        completeness += 0.4
    else:
        missing_fields.append("title")
        issues.append("Missing event title")

    if event.date:
        completeness += 0.3
    else:
        missing_fields.append("date")
        issues.append("Missing event date")

    if event.location_name or event.location_city:
        completeness += 0.3
    else:
        missing_fields.append("location")
        issues.append("Missing location information")

    # Accuracy checks
    accuracy = 1.0
    if event.date and "None" in str(event.date):
        accuracy -= 0.3
        issues.append("Date appears to be None or invalid")

    confidence = 0.5  # Default medium confidence

    overall = (completeness + accuracy + confidence) / 3

    # Decide on deep crawl
    should_deep_crawl = completeness < 0.6 or len(missing_fields) >= 2
    deep_crawl_reason = ""
    if should_deep_crawl:
        deep_crawl_reason = (
            f"Low completeness ({completeness:.2f}) or multiple missing fields"
        )

    return EventQualityScore(
        completeness=completeness,
        accuracy=accuracy,
        confidence=confidence,
        missing_fields=missing_fields,
        issues=issues,
        suggestions=[
            "Try deep crawling linked pages for more details",
            "Check if page requires authentication",
        ],
        overall_score=overall,
        should_deep_crawl=should_deep_crawl,
        deep_crawl_reason=deep_crawl_reason,
    )


async def optimize_event_extraction(
    original_content: str,
    url: str,
    current_event: "EventDetails",
    quality_score: EventQualityScore,
    max_iterations: int = 3,
) -> Tuple["EventDetails", EventQualityScore]:
    """
    Optimize event extraction based on evaluation feedback.

    Uses the evaluator's feedback to re-extract or refine event data,
    iterating until quality threshold is met or max iterations reached.

    Args:
        original_content: Original scraped content
        url: Event URL
        current_event: Current extracted event
        quality_score: Current quality evaluation
        max_iterations: Maximum optimization iterations

    Returns:
        Tuple of (optimized_event, final_quality_score)
    """
    import os
    from openai import AsyncOpenAI
    import json
    from ...models.events import EventDetails

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    client = AsyncOpenAI(api_key=api_key)

    iteration = 0
    best_event = current_event
    best_score = quality_score

    while iteration < max_iterations and not quality_score.is_acceptable():
        iteration += 1
        print(f"\n🔄 Optimization iteration {iteration}/{max_iterations}")
        print(f"   Current score: {quality_score.overall_score:.2f}")
        print(f"   Issues: {', '.join(quality_score.issues)}")

        # Build optimization prompt with feedback
        current_data = current_event.model_dump()

        prompt = f"""You are an expert at extracting event information. Re-extract event details with improvements.

ORIGINAL CONTENT:
{original_content[:4000]}

CURRENT EXTRACTION (needs improvement):
{json.dumps(current_data, indent=2)}

EVALUATION FEEDBACK:
- Completeness: {quality_score.completeness:.2f}
- Accuracy: {quality_score.accuracy:.2f}
- Confidence: {quality_score.confidence:.2f}
- Missing fields: {', '.join(quality_score.missing_fields)}
- Issues identified: {', '.join(quality_score.issues)}
- Suggestions: {', '.join(quality_score.suggestions)}

TASK: Re-extract the event information, paying special attention to the identified issues.
Focus on finding the missing fields and correcting any inaccuracies.

Return a complete JSON object matching the EventDetails schema with ALL fields.
Look more carefully in the content for:
{', '.join(quality_score.missing_fields) if quality_score.missing_fields else 'any missing information'}

Return ONLY the JSON object with all event fields."""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert event data extractor. Return only valid JSON matching EventDetails schema.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )

            result_text = response.choices[0].message.content

            # Extract JSON
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1

            if start_idx == -1 or end_idx <= start_idx:
                print("   ⚠️ No JSON in response")
                break

            json_text = result_text[start_idx:end_idx]
            data = json.loads(json_text)

            # Create improved event
            improved_event = EventDetails(**data)

            # Ensure URL is set
            if not improved_event.url or improved_event.url == "":
                improved_event.url = url

            # Re-evaluate
            new_quality = await evaluate_event_quality(improved_event, original_content)

            print(f"   ✅ New score: {new_quality.overall_score:.2f}")

            # Keep if improved
            if new_quality.overall_score > best_score.overall_score:
                best_event = improved_event
                best_score = new_quality
                print(f"   🎉 Improved! ({best_score.overall_score:.2f})")

            current_event = improved_event
            quality_score = new_quality

        except Exception as e:
            print(f"   ❌ Optimization iteration {iteration} failed: {e}")
            break

    return best_event, best_score


async def extract_event_with_quality_control(
    url: str, content: str, quality_threshold: float = 0.7, max_iterations: int = 3
) -> Tuple["EventDetails", EventQualityScore]:
    """
    Extract event details with evaluator-optimizer quality control.

    This implements the full evaluator-optimizer pattern:
    1. Extract initial event data
    2. Evaluate quality
    3. If quality is low, optimize and re-extract
    4. Repeat until quality threshold met or max iterations

    Args:
        url: Event URL
        content: Scraped content
        quality_threshold: Minimum acceptable quality score (0-1)
        max_iterations: Maximum optimization iterations

    Returns:
        Tuple of (final_event, final_quality_score)

    Example:
        event, quality = await extract_event_with_quality_control(
            url="https://example.com/event",
            content=scraped_text,
            quality_threshold=0.8
        )

        if quality.is_acceptable():
            print(f"High quality extraction: {event.title}")
        else:
            print(f"Low quality (score: {quality.overall_score})")
            print(f"Issues: {quality.issues}")
    """
    from ...agents.extract_structured_data import extract_event_details

    print("🎯 Starting event extraction with quality control...")

    # Step 1: Initial extraction
    print("📊 Step 1: Initial extraction...")
    event = await extract_event_details(text=content, url=url)
    print(f"   Extracted: {event.title}")

    # Step 2: Evaluate quality
    print("🔍 Step 2: Evaluating quality...")
    quality = await evaluate_event_quality(event, content)
    print(f"   Quality score: {quality.overall_score:.2f}")
    print(f"   Completeness: {quality.completeness:.2f}")
    print(f"   Accuracy: {quality.accuracy:.2f}")
    print(f"   Confidence: {quality.confidence:.2f}")

    if quality.issues:
        print(f"   Issues: {', '.join(quality.issues)}")

    # Step 3: Optimize if needed
    if not quality.is_acceptable(quality_threshold):
        print(f"⚠️  Quality below threshold ({quality_threshold:.2f}), optimizing...")
        event, quality = await optimize_event_extraction(
            content, url, event, quality, max_iterations
        )
        print(f"✅ Final quality score: {quality.overall_score:.2f}")
    else:
        print(
            f"✅ Quality acceptable ({quality.overall_score:.2f} >= {quality_threshold:.2f})"
        )

    return event, quality
