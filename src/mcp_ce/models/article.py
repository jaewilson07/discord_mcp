"""Article model for crawled web content."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Article(BaseModel):
    """
    Represents a crawled article or web page.

    This model holds the structured data extracted from a web page,
    including content, metadata, and media references.
    """

    url: str = Field(..., description="Source URL of the article")
    title: str = Field(default="", description="Article title")
    description: str = Field(default="", description="Article description/summary")
    author: str = Field(default="", description="Article author")
    published_date: str = Field(default="", description="Publication date")
    keywords: List[str] = Field(
        default_factory=list, description="Article keywords/tags"
    )

    content_markdown: str = Field(
        ..., description="Full article content in markdown format"
    )
    content_html: Optional[str] = Field(
        default=None, description="Full article content in HTML format"
    )

    images: List[Dict[str, Any]] = Field(
        default_factory=list, description="Extracted images with src, alt, score"
    )
    links: Dict[str, List[str]] = Field(
        default_factory=lambda: {"internal": [], "external": []},
        description="Internal and external links",
    )

    extracted_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp of when content was extracted",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "title": "Example Article",
                "description": "This is an example article",
                "author": "John Doe",
                "published_date": "2025-01-15",
                "keywords": ["example", "article"],
                "content_markdown": "# Example Article\n\nContent here...",
                "extracted_at": "2025-01-15T10:30:00",
            }
        }

    async def to_notion(
        self, database_id: str, status: str = "Crawled"
    ) -> Dict[str, Any]:
        """
        Export article to Notion database.

        Calls the atomic save_page_to_notion tool to handle the actual
        Notion API interaction, while this method formats the article
        data appropriately.

        Args:
            database_id: Notion database ID to save to
            status: Status to set in Notion (default: "Crawled")

        Returns:
            Dict with success status and Notion page info
        """
        try:
            from mcp_ce.tools.notion._client_helper import (
                get_data_source_id_from_database,
                query_data_source,
                create_page,
                update_page,
                delete_all_blocks,
                append_blocks,
            )
            from notion_blockify import Blockizer

            # Get data source ID
            data_source_id = await get_data_source_id_from_database(database_id)

            # Check if article already exists by URL
            existing = await query_data_source(
                data_source_id,
                filter_obj={"property": "URL", "url": {"equals": self.url}},
            )

            existing_pages = existing.get("results", [])

            # Prepare markdown content for Notion blocks
            blockizer = Blockizer()

            full_content = f"""## 📝 Summary

{self.description}

---

## 📄 Article Content

{self.content_markdown}
"""

            # Convert markdown to blocks
            blocks = blockizer.convert(full_content)

            # Prepare properties
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": (
                                    self.title[:100]
                                    if self.title
                                    else "Untitled Article"
                                )
                            }
                        }
                    ]
                },
                "URL": {"url": self.url},
                "Status": {"select": {"name": status}},
                "Scrape Date": {"date": {"start": self.extracted_at}},
            }

            # Add optional properties if available
            if self.author:
                properties["Author"] = {
                    "rich_text": [{"text": {"content": self.author}}]
                }

            if self.published_date:
                properties["Published Date"] = {
                    "rich_text": [{"text": {"content": self.published_date}}]
                }

            # Check Lock status if updating
            if existing_pages:
                existing_page = existing_pages[0]
                page_id = existing_page["id"]
                lock_status = (
                    existing_page.get("properties", {})
                    .get("Lock", {})
                    .get("checkbox", False)
                )

                if lock_status:
                    # Page is locked, create new one
                    pass  # Fall through to create
                else:
                    # Update existing page
                    await update_page(page_id, properties)

                    # Delete old blocks and add new content
                    await delete_all_blocks(page_id)

                    # Add blocks in chunks of 100
                    for i in range(0, len(blocks), 100):
                        chunk = blocks[i : i + 100]
                        await append_blocks(page_id, chunk)

                    return {
                        "success": True,
                        "action": "updated",
                        "page_id": page_id,
                        "url": self.url,
                    }

            # Create new page
            # Split blocks if more than 100
            initial_blocks = blocks[:100] if len(blocks) > 100 else blocks
            remaining_blocks = blocks[100:] if len(blocks) > 100 else []

            created_page = await create_page(
                parent_database_id=database_id,
                properties=properties,
                children=initial_blocks,
            )

            page_id = created_page["id"]

            # Append remaining blocks if any
            if remaining_blocks:
                for i in range(0, len(remaining_blocks), 100):
                    chunk = remaining_blocks[i : i + 100]
                    await append_blocks(page_id, chunk)

            return {
                "success": True,
                "action": "created",
                "page_id": page_id,
                "url": self.url,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save to Notion: {str(e)}",
                "url": self.url,
            }
