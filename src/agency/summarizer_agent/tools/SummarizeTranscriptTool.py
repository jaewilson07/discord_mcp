from agency_swarm.tools import BaseTool
from pydantic import Field
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
import os
from dotenv import load_dotenv

load_dotenv()

class SummarizeTranscriptTool(BaseTool):
    """
    Creates a concise summary of a video transcript using AI. Employs map-reduce 
    strategy to handle long transcripts by chunking, summarizing parts, then combining.
    """
    
    transcript: str = Field(
        ...,
        description="Full video transcript text to summarize"
    )
    
    video_title: str = Field(
        ...,
        description="Video title for context"
    )
    
    summary_length: str = Field(
        default="medium",
        description="Desired summary length: 'short' (2-3 sentences), 'medium' (1 paragraph), 'long' (multiple paragraphs)"
    )

    def run(self):
        """
        Generates a summary of the video transcript.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        if not self.transcript.strip():
            return "Error: Transcript cannot be empty"
        
        if self.summary_length not in ["short", "medium", "long"]:
            return "Error: summary_length must be one of: 'short', 'medium', 'long'"
        
        try:
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                api_key=api_key
            )
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200
            )
            
            full_text = f"Video Title: {self.video_title}\n\nTranscript: {self.transcript}"
            
            docs = text_splitter.create_documents([full_text])
            
            chain_type = "stuff" if len(docs) <= 1 else "map_reduce"
            chain = load_summarize_chain(
                llm,
                chain_type=chain_type,
                verbose=False
            )
            
            if self.summary_length == "short":
                prompt_addition = "Provide a brief 2-3 sentence summary of the key points."
            elif self.summary_length == "medium":
                prompt_addition = "Provide a concise one paragraph summary covering the main ideas."
            else:
                prompt_addition = "Provide a detailed summary in multiple paragraphs covering all important points."
            
            docs[0].page_content = prompt_addition + "\n\n" + docs[0].page_content
            
            result = chain.invoke(docs)
            summary = result['output_text']
            
            output = f"Summary of: {self.video_title}\n"
            output += f"Summary length: {self.summary_length}\n"
            output += f"Original transcript length: {len(self.transcript)} characters\n\n"
            output += f"{summary}"
            
            return output
            
        except Exception as e:
            return f"Error summarizing transcript: {str(e)}"


if __name__ == "__main__":
    sample_transcript = "Welcome to this tutorial on machine learning. Today we'll cover neural networks..."
    tool = SummarizeTranscriptTool(
        transcript=sample_transcript,
        video_title="Machine Learning Basics",
        summary_length="short"
    )
    print(tool.run())
