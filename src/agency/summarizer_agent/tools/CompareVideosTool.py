from agency_swarm.tools import BaseTool
from pydantic import Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import json

load_dotenv()

class CompareVideosTool(BaseTool):
    """
    Analyzes multiple video summaries to find common themes, differences, and unique 
    insights across videos.
    """
    
    video_summaries: str = Field(
        ...,
        description="JSON string of array containing summary objects with 'title', 'summary', and 'url' fields"
    )
    
    comparison_criteria: str = Field(
        default=None,
        description="Optional specific aspect to compare (e.g., 'technical accuracy', 'viewpoint', 'completeness')"
    )

    def run(self):
        """
        Compares video summaries and returns analysis.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        try:
            summaries = json.loads(self.video_summaries)
        except json.JSONDecodeError:
            return "Error: video_summaries must be a valid JSON string"
        
        if not isinstance(summaries, list):
            return "Error: video_summaries must be an array"
        
        if len(summaries) < 2:
            return "Error: Need at least 2 video summaries to compare"
        
        for i, summary in enumerate(summaries):
            if not isinstance(summary, dict) or 'title' not in summary or 'summary' not in summary:
                return f"Error: Summary {i+1} must have 'title' and 'summary' fields"
        
        try:
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                api_key=api_key
            )
            
            summaries_text = "\n\n".join([
                f"Video {i+1}: {s['title']}\nSummary: {s['summary']}\nURL: {s.get('url', 'N/A')}"
                for i, s in enumerate(summaries)
            ])
            
            criteria_instruction = ""
            if self.comparison_criteria:
                criteria_instruction = f"\nFocus your comparison on: {self.comparison_criteria}"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert at comparative analysis of content."),
                ("human", f"""Compare and analyze the following video summaries:

{summaries_text}

Provide a comparative analysis including:
1. Common Themes: What topics or ideas appear across multiple videos?
2. Unique Insights: What unique perspectives or information does each video provide?
3. Differences: How do the videos differ in approach, focus, or conclusions?
4. Overall Synthesis: What can we learn from considering all these videos together?
{criteria_instruction}

Structure your response clearly with sections.""")
            ])
            
            chain = prompt | llm
            response = chain.invoke({})
            
            output = f"Comparison Analysis of {len(summaries)} Videos:\n\n"
            output += response.content
            
            return output
            
        except Exception as e:
            return f"Error comparing videos: {str(e)}"


if __name__ == "__main__":
    sample_summaries = json.dumps([
        {
            "title": "Intro to Neural Networks",
            "summary": "Basic overview of neural network architecture",
            "url": "https://youtube.com/watch?v=example1"
        },
        {
            "title": "Deep Learning Explained",
            "summary": "Advanced explanation of deep learning concepts",
            "url": "https://youtube.com/watch?v=example2"
        }
    ])
    tool = CompareVideosTool(video_summaries=sample_summaries)
    print(tool.run())
