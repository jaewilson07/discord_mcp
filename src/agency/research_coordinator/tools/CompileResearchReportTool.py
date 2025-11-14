from agency_swarm.tools import BaseTool
from pydantic import Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import json

load_dotenv()

class CompileResearchReportTool(BaseTool):
    """
    Synthesizes all gathered information into a comprehensive research report.
    Combines video summaries, key insights, and web research into structured document with citations.
    """
    
    research_topic: str = Field(
        ...,
        description="Original research question or topic"
    )
    
    video_insights: str = Field(
        ...,
        description="JSON string of array containing video insights with 'title', 'url', 'summary', and optional 'key_points'"
    )
    
    additional_context: str = Field(
        default=None,
        description="Optional supplementary information from web research or other sources"
    )
    
    report_format: str = Field(
        default="standard",
        description="Report format: 'executive_summary' (brief), 'standard' (balanced), 'detailed' (comprehensive)"
    )

    def run(self):
        """
        Compiles and returns a research report.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        if not self.research_topic.strip():
            return "Error: research_topic cannot be empty"
        
        if self.report_format not in ["executive_summary", "standard", "detailed"]:
            return "Error: report_format must be one of: 'executive_summary', 'standard', 'detailed'"
        
        try:
            insights = json.loads(self.video_insights)
        except json.JSONDecodeError:
            return "Error: video_insights must be a valid JSON string"
        
        if not isinstance(insights, list) or len(insights) == 0:
            return "Error: video_insights must be a non-empty array"
        
        try:
            llm = ChatOpenAI(
                model_name="gpt-4o",
                temperature=0.2,
                api_key=api_key
            )
            
            insights_text = ""
            for i, insight in enumerate(insights, 1):
                insights_text += f"\n\nSource {i}: {insight.get('title', 'Unknown')}\n"
                insights_text += f"URL: {insight.get('url', 'N/A')}\n"
                if 'summary' in insight:
                    insights_text += f"Summary: {insight['summary']}\n"
                if 'key_points' in insight:
                    insights_text += f"Key Points:\n"
                    if isinstance(insight['key_points'], list):
                        for point in insight['key_points']:
                            insights_text += f"  - {point}\n"
                    else:
                        insights_text += f"  {insight['key_points']}\n"
            
            additional_text = ""
            if self.additional_context:
                additional_text = f"\n\nAdditional Context:\n{self.additional_context}"
            
            format_instructions = {
                "executive_summary": "Create a brief executive summary (1-2 pages) with key findings and recommendations.",
                "standard": "Create a balanced report (3-5 pages) with introduction, findings, analysis, and conclusions.",
                "detailed": "Create a comprehensive report (5-10 pages) with in-depth analysis, multiple sections, and detailed citations."
            }
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a professional research analyst who creates well-structured, insightful research reports."),
                ("human", f"""Create a {self.report_format} research report on the following topic:

Research Topic: {self.research_topic}

Video Sources Analyzed: {len(insights)}

{insights_text}
{additional_text}

{format_instructions[self.report_format]}

Structure your report with:
1. Executive Summary / Introduction
2. Key Findings (organized by theme)
3. Analysis and Insights
4. Conclusions and Recommendations
5. Sources/References

Use markdown formatting. Include citations to specific videos when referencing information.
Make the report professional, well-organized, and actionable.""")
            ])
            
            chain = prompt | llm
            response = chain.invoke({})
            
            header = f"# Research Report: {self.research_topic}\n\n"
            header += f"**Report Type:** {self.report_format.replace('_', ' ').title()}\n"
            header += f"**Sources Analyzed:** {len(insights)} videos\n"
            header += f"**Date:** {self._get_date()}\n\n"
            header += "---\n\n"
            
            output = header + response.content
            
            return output
            
        except Exception as e:
            return f"Error compiling research report: {str(e)}"
    
    def _get_date(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")


if __name__ == "__main__":
    sample_insights = json.dumps([
        {
            "title": "Multi-Agent Systems Overview",
            "url": "https://youtube.com/watch?v=example1",
            "summary": "Explains the basics of multi-agent systems",
            "key_points": ["Agents can communicate", "Coordination is key"]
        }
    ])
    tool = CompileResearchReportTool(
        research_topic="Multi-agent AI systems",
        video_insights=sample_insights,
        report_format="standard"
    )
    print(tool.run())
