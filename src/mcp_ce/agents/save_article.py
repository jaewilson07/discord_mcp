"""Save extracted article content to a local JSON file with metadata."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from registry import register_command
import hashlib


@register_command("crawl4ai", "save_article")
async def save_article(
    url: str,
    title: str,
    content: str,
    description: str = "",
    author: str = "",
    published_date: str = "",
    keywords: Optional[List[str]] = None,
    images: Optional[List[Dict[str, Any]]] = None,
    links: Optional[Dict[str, List[str]]] = None,
    custom_filename: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save extracted article content to a local JSON file.

    This tool organizes and persists crawled article data in a structured JSON format,
    including content, metadata, and extraction details. Files are saved with timestamps
    and unique identifiers.

    Args:
        url: The URL of the article being saved
        title: The title of the article
        content: The main article content in markdown format
        description: A brief description or summary of the article
        author: The author of the article
        published_date: The publication date (if available)
        keywords: List of keywords or tags associated with the article
        images: List of images found in the article
        links: Dictionary of internal and external links
        custom_filename: Optional custom filename (without extension)
        output_dir: Optional output directory path (defaults to ./articles)

    Returns:
        Dict containing:
        - success: bool indicating if save succeeded
        - filepath: the full path to the saved file
        - filename: the filename used
        - article_id: unique ID generated for the article
        - title: article title
        - content_length: length of content in characters
        - saved_at: ISO timestamp of save operation
        - error: error message if save failed
    """
    try:
        # Set default values
        if keywords is None:
            keywords = []
        if images is None:
            images = []
        if links is None:
            links = {}

        # Determine output directory
        if output_dir:
            files_folder = Path(output_dir)
        else:
            # Default to ./articles in current working directory
            files_folder = Path.cwd() / "articles"

        files_folder.mkdir(exist_ok=True, parents=True)

        # Generate a unique article ID based on URL
        article_id = hashlib.md5(url.encode()).hexdigest()[:12]

        # Generate filename
        if custom_filename:
            filename = f"{custom_filename}.json"
        elif title:
            # Sanitize title for filename
            safe_title = "".join(
                c for c in title if c.isalnum() or c in (" ", "-", "_")
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
            "url": url,
            "title": title,
            "description": description,
            "author": author,
            "published_date": published_date,
            "keywords": keywords,
            "content": content,
            "content_length": len(content),
            "images": images,
            "links": links,
            "metadata": {
                "extracted_at": datetime.now().isoformat(),
                "saved_at": datetime.now().isoformat(),
                "file_version": "1.0",
            },
        }

        # Save to JSON file with pretty formatting
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article_data, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "message": "Article saved successfully",
            "filepath": str(filepath),
            "filename": filename,
            "article_id": article_id,
            "title": title,
            "content_length": len(content),
            "saved_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}


# Test code
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await save_article(
            url="https://example.com/article",
            title="Example Article",
            content="# Example Article\n\nThis is the article content in markdown format.",
            description="An example article for testing",
            author="John Doe",
            keywords=["example", "test", "article"],
        )

        print(f"Success: {result['success']}")
        if result["success"]:
            print(f"Filepath: {result['filepath']}")
            print(f"Article ID: {result['article_id']}")
            print(f"Content length: {result['content_length']}")
        else:
            print(f"Error: {result['error']}")

    asyncio.run(test())
