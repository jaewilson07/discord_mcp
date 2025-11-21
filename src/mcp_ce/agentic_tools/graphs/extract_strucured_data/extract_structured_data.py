"""
Generic AI-powered data extraction tool.
Extracts structured data from text using OpenAI and Pydantic models.
"""

import os
import json
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

T = TypeVar("T", bound=BaseModel)


async def extract_structured_data(
    text: str,
    model_class: Type[T],
    instructions: Optional[str] = None,
    openai_model: str = "gpt-4o",
) -> T:
    """
    Extract structured data from text using AI and a Pydantic model.

    This tool uses OpenAI to parse unstructured text and extract information
    according to a Pydantic model schema. It's useful for extracting events,
    articles, products, or any structured data from web pages or documents.

    Args:
        text: The unstructured text to extract data from
        model_class: Pydantic model class defining the structure to extract
        instructions: Optional custom instructions for extraction
        openai_model: OpenAI model to use (default: gpt-4o)

    Returns:
        Instance of model_class with extracted data

    Raises:
        ValueError: If OPENAI_API_KEY not configured
        RuntimeError: If extraction fails

    Example:
        from mcp_ce.models.events import EventDetails

        event = await extract_structured_data(
            text=scraped_content,
            model_class=EventDetails,
            instructions="Extract all event details from this Facebook page"
        )
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    client = AsyncOpenAI(api_key=api_key)

    # Get model schema
    schema = model_class.model_json_schema()

    # Build field descriptions for the prompt
    field_descriptions = []
    for field_name, field_info in schema.get("properties", {}).items():
        desc = field_info.get("description", "")
        field_type = field_info.get("type", "")
        if "anyOf" in field_info:
            # Handle Optional fields
            types = [t.get("type") for t in field_info["anyOf"] if "type" in t]
            field_type = f"Optional[{' | '.join(types)}]"

        required = field_name in schema.get("required", [])
        req_marker = "REQUIRED" if required else "optional"

        field_descriptions.append(
            f"- {field_name} ({field_type}, {req_marker}): {desc}"
        )

    fields_text = "\n".join(field_descriptions)

    # Build system prompt
    system_prompt = f"""You are an expert at extracting structured information from text.
Extract data according to the provided schema and return ONLY valid JSON.
Be thorough and capture every piece of information available.

{instructions or 'Extract all available information from the provided text.'}"""

    # Build user prompt
    user_prompt = f"""Extract structured data from the following text according to this schema:

{fields_text}

Rules:
- Return ONLY a JSON object matching the schema
- Set missing fields to null (not 'null' string, but actual null)
- For boolean fields, use true/false
- For number fields, use integers/floats without quotes
- Be comprehensive - extract ALL available information
- If information is not found, set field to null

Text to extract from:
{text[:12000]}

Return JSON:"""

    try:
        response = await client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        result_text = response.choices[0].message.content

        # Extract JSON from response
        start_idx = result_text.find("{")
        end_idx = result_text.rfind("}") + 1

        if start_idx == -1 or end_idx <= start_idx:
            raise RuntimeError("AI did not return valid JSON")

        json_text = result_text[start_idx:end_idx]
        data = json.loads(json_text)

        # Create and validate Pydantic model instance
        return model_class(**data)

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from AI response: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract structured data: {e}")


async def extract_event_details(text: str, url: str):
    """
    Convenience function for extracting event details.

    Args:
        text: Scraped event page content
        url: Event URL

    Returns:
        EventDetails instance
    """
    from ....models.events import EventDetails

    # Add URL context to instructions
    instructions = f"""Extract comprehensive event information.
The event URL is: {url}
Make sure to include the URL in the returned data."""

    try:
        event = await extract_structured_data(
            text=text, model_class=EventDetails, instructions=instructions
        )

        # Ensure URL is set
        if not event.url or event.url == "":
            event.url = url

        return event

    except Exception as e:
        # Fallback: create minimal event details
        return EventDetails(
            title="Event (extraction failed)",
            description=text[:500] if text else "No description available",
            url=url,
        )
