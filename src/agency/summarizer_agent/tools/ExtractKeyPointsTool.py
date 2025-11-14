from agency_swarm.tools import BaseTool
from pydantic import Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import os
from dotenv import load_dotenv
import json

load_dotenv()

class ExtractKeyPointsTool(BaseTool):
    """
    Analyzes transcript and extracts main ideas, important facts, and key takeaways 
    as a structured list.
    """
    
    transcript: str = Field(
        ...,
        description="Full video transcript text to analyze"
    )
    
    max_points: int = Field(
        default=10,
        description="Maximum number of key points to extract (3-20)",
        ge=3,
        le=20
    )
    
    focus_area: str = Field(
        default=None,
        description="Optional specific topic to focus extraction on (e.g., 'technical implementation', 'business strategy')"
    )

    def run(self):
        """
        Extracts and returns key points from the transcript.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        if not self.transcript.strip():
            return "Error: Transcript cannot be empty"
        
        try:
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                api_key=api_key
            )
            
            focus_instruction = ""
            if self.focus_area:
                focus_instruction = f"\nFocus especially on points related to: {self.focus_area}"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert at analyzing content and extracting key points."),
                ("human", f"""Analyze the following transcript and extract the {self.max_points} most important key points.
                
Each key point should be:
- Clear and concise (1-2 sentences max)
- Capture a distinct idea or fact
- Be actionable or informative
{focus_instruction}

Return your response as a JSON object with a 'key_points' field containing an array of strings.

Transcript:
{self.transcript}

Return ONLY the JSON object, no other text.""")
            ])
            
            chain = prompt | llm
            response = chain.invoke({})
            
            try:
                response_text = response.content
                
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
                    result = json.loads(json_text)
                    key_points = result.get('key_points', [])
                else:
                    return "Error: Could not parse JSON from response"
                
            except json.JSONDecodeError:
                lines = response.content.split('\n')
                key_points = [line.strip('- •*') for line in lines if line.strip() and line.strip()[0] in ['-', '•', '*', '1', '2', '3', '4', '5', '6', '7', '8', '9']]
            
            if not key_points:
                return "Error: No key points extracted from transcript"
            
            output = f"Extracted {len(key_points)} key points:\n\n"
            for i, point in enumerate(key_points, 1):
                output += f"{i}. {point}\n\n"
            
            if self.focus_area:
                output = f"Key points (focused on: {self.focus_area}):\n\n" + output
            
            return output
            
        except Exception as e:
            return f"Error extracting key points: {str(e)}"


if __name__ == "__main__":
    sample_transcript = "In this video, we discuss neural networks, backpropagation, and gradient descent..."
    tool = ExtractKeyPointsTool(
        transcript=sample_transcript,
        max_points=5,
        focus_area="technical concepts"
    )
    print(tool.run())
