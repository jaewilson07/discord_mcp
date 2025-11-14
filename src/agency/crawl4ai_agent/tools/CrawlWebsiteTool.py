from agency_swarm.tools import BaseTool
from pydantic import Field
import asyncio
import json
from typing import Optional, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from datetime import datetime


class CrawlWebsiteTool(BaseTool):
    """
    A powerful tool for crawling websites and extracting clean, structured content using Crawl4AI.

    This tool uses advanced web crawling techniques to extract article content, metadata,
    and media from web pages. It handles dynamic content, JavaScript-heavy sites, and
    provides clean markdown output optimized for LLM consumption.
    """

    url: str = Field(
        ...,
        description="The URL of the website to crawl and extract content from.",
    )

    extract_images: bool = Field(
        default=True,
        description="Whether to extract image URLs from the page.",
    )

    extract_links: bool = Field(
        default=True,
        description="Whether to extract internal and external links from the page.",
    )

    word_count_threshold: int = Field(
        default=10,
        description="Minimum word count for content blocks to be included (filters out noise).",
    )

    headless: bool = Field(
        default=True,
        description="Whether to run the browser in headless mode (no visible window).",
    )

    def run(self) -> str:
        """
        Crawls the website and extracts structured content.

        Returns:
            A JSON string containing the extracted content and metadata.
        """
        try:
            # Run the async crawl function
            result = asyncio.run(self._crawl_async())
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps(
                {"success": False, "error": str(e), "url": self.url}, indent=2
            )

    async def _crawl_async(self) -> Dict[str, Any]:
        """
        Async method that performs the actual crawling using Crawl4AI.
        """
        # Configure the browser
        browser_config = BrowserConfig(
            headless=self.headless,
            verbose=False,
        )

        # Configure the markdown generator with content filtering
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=self.word_count_threshold,
            )
        )

        # Configure the crawler run
        crawler_config = CrawlerRunConfig(
            markdown_generator=markdown_generator,
            cache_mode=CacheMode.BYPASS,  # Always fetch fresh content
        )

        # Perform the crawl
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=self.url, config=crawler_config)

            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message or "Unknown error occurred",
                    "url": self.url,
                }

            # Extract metadata
            metadata = {}
            if hasattr(result, "metadata") and result.metadata:
                metadata = result.metadata

            # Build the response
            response = {
                "success": True,
                "url": result.url,
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "author": metadata.get("author", ""),
                "published_date": metadata.get("published_date", ""),
                "keywords": metadata.get("keywords", []),
                "content": {
                    "markdown": (
                        result.markdown.raw_markdown
                        if hasattr(result.markdown, "raw_markdown")
                        else result.markdown
                    ),
                    "markdown_length": (
                        len(result.markdown.raw_markdown)
                        if hasattr(result.markdown, "raw_markdown")
                        else len(result.markdown)
                    ),
                    "fit_markdown": (
                        result.markdown.fit_markdown
                        if hasattr(result.markdown, "fit_markdown")
                        else None
                    ),
                },
                "extracted_at": datetime.now().isoformat(),
            }

            # Add images if requested
            if self.extract_images and hasattr(result, "media") and result.media:
                images = []
                if "images" in result.media:
                    for img in result.media["images"]:
                        if isinstance(img, dict):
                            images.append(
                                {
                                    "src": img.get("src", ""),
                                    "alt": img.get("alt", ""),
                                    "score": img.get("score", 0),
                                }
                            )
                response["images"] = images

            # Add links if requested
            if self.extract_links and hasattr(result, "links") and result.links:
                links = {
                    "internal": result.links.get("internal", []),
                    "external": result.links.get("external", []),
                }
                response["links"] = links

            return response


if __name__ == "__main__":
    # Test the tool
    tool = CrawlWebsiteTool(
        url="https://www.example.com", extract_images=True, extract_links=True
    )
    result = tool.run()
    print(result)
