from agency_swarm.tools import BaseTool
from pydantic import Field
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib


class SaveArticleTool(BaseTool):
    """
    Saves extracted article content to a local JSON file with comprehensive metadata.

    This tool organizes and persists crawled article data in a structured JSON format,
    including content, metadata, and extraction details. Files are saved in the agent's
    files folder with timestamps and unique identifiers.
    """

    url: str = Field(
        ...,
        description="The URL of the article being saved.",
    )

    title: str = Field(
        ...,
        description="The title of the article.",
    )

    content: str = Field(
        ...,
        description="The main article content in markdown format.",
    )

    description: Optional[str] = Field(
        default="",
        description="A brief description or summary of the article.",
    )

    author: Optional[str] = Field(
        default="",
        description="The author of the article.",
    )

    published_date: Optional[str] = Field(
        default="",
        description="The publication date of the article (if available).",
    )

    keywords: Optional[List[str]] = Field(
        default_factory=list,
        description="List of keywords or tags associated with the article.",
    )

    images: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="List of images found in the article with their URLs and alt text.",
    )

    links: Optional[Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Dictionary of internal and external links found in the article.",
    )

    custom_filename: Optional[str] = Field(
        default=None,
        description="Optional custom filename (without extension). If not provided, will be generated from title or URL.",
    )

    def run(self) -> str:
        """
        Saves the article to a JSON file in the files folder.

        Returns:
            A success message with the file path or an error message.
        """
        try:
            # Get the files folder path (relative to this tool)
            current_dir = Path(__file__).parent.parent
            files_folder = current_dir / "files"
            files_folder.mkdir(exist_ok=True)

            # Generate a unique article ID based on URL
            article_id = hashlib.md5(self.url.encode()).hexdigest()[:12]

            # Generate filename
            if self.custom_filename:
                filename = f"{self.custom_filename}.json"
            elif self.title:
                # Sanitize title for filename
                safe_title = "".join(
                    c for c in self.title if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                safe_title = safe_title[:50]  # Limit length
                filename = f"{safe_title}_{article_id}.json"
            else:
                # Use article ID if no title
                filename = f"article_{article_id}.json"

            filepath = files_folder / filename

            # Build the article data structure
            article_data = {
                "id": article_id,
                "url": self.url,
                "title": self.title,
                "description": self.description,
                "author": self.author,
                "published_date": self.published_date,
                "keywords": self.keywords,
                "content": self.content,
                "content_length": len(self.content),
                "images": self.images,
                "links": self.links,
                "metadata": {
                    "extracted_at": datetime.now().isoformat(),
                    "saved_at": datetime.now().isoformat(),
                    "file_version": "1.0",
                },
            }

            # Save to JSON file with pretty formatting
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(article_data, f, indent=2, ensure_ascii=False)

            # Return success message
            return json.dumps(
                {
                    "success": True,
                    "message": f"Article saved successfully",
                    "filepath": str(filepath),
                    "filename": filename,
                    "article_id": article_id,
                    "title": self.title,
                    "content_length": len(self.content),
                    "saved_at": datetime.now().isoformat(),
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {"success": False, "error": str(e), "url": self.url}, indent=2
            )


if __name__ == "__main__":
    # Test the tool
    tool = SaveArticleTool(
        url="https://example.com/article",
        title="Example Article",
        content="# Example Article\n\nThis is the article content in markdown format.",
        description="An example article for testing",
        author="John Doe",
        keywords=["example", "test", "article"],
    )
    result = tool.run()
    print(result)
