"""
Generate structured research plans for YouTube video investigation.
"""

import os
import json
from typing import Dict, Any, Optional, List, Union, Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime


async def create_youtube_research_plan(
    research_topic: str,
    scope: Literal["quick", "moderate", "comprehensive"] = "comprehensive",
    specific_questions: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Generate a structured research plan for investigating a topic via YouTube videos.

    Defines search strategy, source selection criteria, analysis approach,
    and expected deliverables.

    Args:
        research_topic: Main research question or topic to investigate
        scope: Research scope determining number of videos:
              - 'quick': 1-3 videos
              - 'moderate': 5-10 videos
              - 'comprehensive': 15-25 videos
        specific_questions: Optional list of specific questions to answer,
                          can be JSON string or list

    Returns:
        Dict containing:
        - success: bool indicating if plan generation succeeded
        - plan: the structured research plan text with sections for:
               - Search Strategy
               - Video Selection Criteria
               - Analysis Approach
               - Deliverables
               - Estimated Time
        - research_topic: the topic being researched
        - scope: the scope level used
        - target_videos: dict with min and max video counts
        - error: error message if generation failed
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "plan": None,
            "error": "OPENAI_API_KEY not found in environment variables",
        }

    if not research_topic.strip():
        return {
            "success": False,
            "plan": None,
            "error": "research_topic cannot be empty",
        }

    if scope not in ["quick", "moderate", "comprehensive"]:
        return {
            "success": False,
            "plan": None,
            "error": "scope must be one of: 'quick', 'moderate', 'comprehensive'",
        }

    video_counts = {"quick": (1, 3), "moderate": (5, 10), "comprehensive": (15, 25)}

    min_videos, max_videos = video_counts[scope]

    # Parse specific questions
    specific_q = []
    if specific_questions:
        try:
            if isinstance(specific_questions, str):
                specific_q = json.loads(specific_questions)
            else:
                specific_q = specific_questions
        except:
            pass

    try:
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3, api_key=api_key)

        questions_text = ""
        if specific_q:
            questions_text = f"\n\nSpecific questions to answer:\n" + "\n".join(
                [f"- {q}" for q in specific_q]
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a research methodology expert who designs effective research plans.",
                ),
                (
                    "human",
                    f"""Create a detailed research plan for the following topic:

Topic: {research_topic}
Scope: {scope} ({min_videos}-{max_videos} videos)
{questions_text}

Provide a structured research plan including:

1. SEARCH STRATEGY
   - 3-5 specific search queries to use on YouTube
   - Keywords and phrases to include
   - Filters or criteria for selecting videos

2. VIDEO SELECTION CRITERIA
   - What types of videos to prioritize (tutorials, explanations, case studies, etc.)
   - Quality indicators to look for
   - Recommended number of videos: {min_videos}-{max_videos}

3. ANALYSIS APPROACH
   - How to analyze the content
   - What aspects to focus on
   - How to synthesize findings

4. DELIVERABLES
   - What the final report should include
   - Structure and format
   - Key sections

5. ESTIMATED TIME
   - Approximate time to complete

Format your response clearly with these sections.""",
                ),
            ]
        )

        chain = prompt | llm
        response = chain.invoke({})

        return {
            "success": True,
            "plan": response.content,
            "research_topic": research_topic,
            "scope": scope,
            "target_videos": {"min": min_videos, "max": max_videos},
            "specific_questions": specific_q if specific_q else None,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "plan": None,
            "error": f"Error creating research plan: {str(e)}",
        }


# Test code
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await create_research_plan(
            research_topic="Multi-agent AI systems with LangChain",
            scope="moderate",
            specific_questions=[
                "How do agents communicate?",
                "What are best practices?",
            ],
        )

        print(f"Success: {result['success']}")
        if result["success"]:
            print(f"\nResearch Plan for: {result['research_topic']}")
            print(
                f"Scope: {result['scope']} ({result['target_videos']['min']}-{result['target_videos']['max']} videos)"
            )
            print("\n" + "=" * 60)
            print(result["plan"])
        else:
            print(f"Error: {result['error']}")

    asyncio.run(test())
