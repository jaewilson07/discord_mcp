"""
Direct YouTube Video Analysis Script
Analyzes https://www.youtube.com/watch?v=SJi469BuU6g without the full agency system
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

# Import the tools directly
from agency.youtube_agent.tools.GetTranscriptTool import GetTranscriptTool
from agency.youtube_agent.tools.GetVideoMetadataTool import GetVideoMetadataTool
from agency.summarizer_agent.tools.ExtractKeyPointsTool import ExtractKeyPointsTool

def analyze_video():
    """Analyze the YouTube video"""
    
    video_url = "https://www.youtube.com/watch?v=SJi469BuU6g&t=321s"
    video_id = "SJi469BuU6g"
    
    print("=" * 80)
    print("YouTube Video Analysis")
    print("=" * 80)
    print(f"\nVideo URL: {video_url}")
    print(f"Video ID: {video_id}\n")
    
    # Step 1: Get video metadata
    print("\n" + "="*80)
    print("STEP 1: Getting Video Metadata...")
    print("="*80)
    metadata_tool = GetVideoMetadataTool(video_id=video_id)
    metadata = metadata_tool.run()
    print(metadata)
    
    # Step 2: Get transcript
    print("\n" + "="*80)
    print("STEP 2: Extracting Transcript...")
    print("="*80)
    transcript_tool = GetTranscriptTool(video_id=video_id)
    transcript_result = transcript_tool.run()
    print(f"Transcript extracted: {len(transcript_result)} characters")
    print("\nFirst 500 characters of transcript:")
    print(transcript_result[:500] + "...")
    
    # Step 3: Extract key points
    print("\n" + "="*80)
    print("STEP 3: Extracting Key Findings (Detailed Analysis)...")
    print("="*80)
    
    # Extract transcript text only (remove metadata)
    transcript_text = transcript_result.split("Transcript:\n")[-1] if "Transcript:\n" in transcript_result else transcript_result
    
    key_points_tool = ExtractKeyPointsTool(
        transcript=transcript_text,
        max_points=15  # Get detailed findings
    )
    key_points = key_points_tool.run()
    print(key_points)
    
    # Step 4: Create final report
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    print(f"""
# YouTube Video Analysis Report

## Video Information
- **URL**: {video_url}
- **Video ID**: {video_id}
- **Analysis Date**: 2025-11-14

---

## Video Metadata
{metadata}

---

## Key Findings (Detailed Analysis)

{key_points}

---

## Full Transcript
Length: {len(transcript_text)} characters

{transcript_text[:2000]}...

[Full transcript available - truncated for brevity]

---

## Source
**Video Link**: [{video_url}]({video_url})

---

*Analysis performed by YouTube Research Agency*
*Powered by OpenAI GPT-4 and YouTube Transcript API*
""")

if __name__ == "__main__":
    try:
        analyze_video()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. YOUTUBE_API_KEY in your .env file")
        print("2. OPENAI_API_KEY in your .env file")
        print("\nGet YouTube API key from: https://console.cloud.google.com/")
