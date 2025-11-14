from agency_swarm.tools import BaseTool
from pydantic import Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import json

load_dotenv()

class CreateResearchPlanTool(BaseTool):
    """
    Generates a structured research plan based on user's research question or topic.
    Defines search strategy, number of sources, analysis approach, and expected deliverables.
    """
    
    research_topic: str = Field(
        ...,
        description="Main research question or topic to investigate"
    )
    
    scope: str = Field(
        default="comprehensive",
        description="Research scope: 'quick' (1-3 videos), 'moderate' (5-10 videos), 'comprehensive' (15-25 videos)"
    )
    
    specific_questions: str = Field(
        default=None,
        description="Optional JSON array of specific questions to answer (e.g., '[\"What is X?\", \"How does Y work?\"]')"
    )

    def run(self):
        """
        Creates and returns a research plan.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        if not self.research_topic.strip():
            return "Error: research_topic cannot be empty"
        
        if self.scope not in ["quick", "moderate", "comprehensive"]:
            return "Error: scope must be one of: 'quick', 'moderate', 'comprehensive'"
        
        video_counts = {
            "quick": (1, 3),
            "moderate": (5, 10),
            "comprehensive": (15, 25)
        }
        
        min_videos, max_videos = video_counts[self.scope]
        
        specific_q = []
        if self.specific_questions:
            try:
                specific_q = json.loads(self.specific_questions)
            except:
                pass
        
        try:
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.3,
                api_key=api_key
            )
            
            questions_text = ""
            if specific_q:
                questions_text = f"\n\nSpecific questions to answer:\n" + "\n".join([f"- {q}" for q in specific_q])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a research methodology expert who designs effective research plans."),
                ("human", f"""Create a detailed research plan for the following topic:

Topic: {self.research_topic}
Scope: {self.scope} ({min_videos}-{max_videos} videos)
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

Format your response clearly with these sections.""")
            ])
            
            chain = prompt | llm
            response = chain.invoke({})
            
            output = f"Research Plan: {self.research_topic}\n"
            output += f"Scope: {self.scope.upper()}\n"
            output += f"Target Videos: {min_videos}-{max_videos}\n"
            output += "="*60 + "\n\n"
            output += response.content
            
            return output
            
        except Exception as e:
            return f"Error creating research plan: {str(e)}"


if __name__ == "__main__":
    tool = CreateResearchPlanTool(
        research_topic="Multi-agent AI systems with LangChain",
        scope="moderate",
        specific_questions='["How do agents communicate?", "What are best practices?"]'
    )
    print(tool.run())
