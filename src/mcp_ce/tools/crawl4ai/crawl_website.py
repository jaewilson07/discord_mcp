"""Crawl websites and extract clean, structured content using Crawl4AI.

This tool extracts raw markdown/HTML content from web pages.
To convert to structured Article format and save to Notion, use an agent.
"""

from typing import Optional, List
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.crawl4ai.models import CrawlResult
from ._helpers import detect_url_type, parse_sitemap, normalize_url

# Suppress Pydantic deprecation warnings from crawl4ai
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="crawl4ai")

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from playwright.async_api import Page, BrowserContext
from datetime import datetime


@register_command("crawl4ai", "crawl_website")
@cache_tool(ttl=3600, id_param="url")  # Cache for 1 hour
async def crawl_website(
    url: str,
    extract_images: bool = True,
    extract_links: bool = True,
    word_count_threshold: int = 10,
    headless: bool = True,
    cookies: Optional[list] = None,
    storage_state: Optional[str] = None,
    wait_for_selector: Optional[str] = None,
    js_code: Optional[str] = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Crawl a website and extract clean markdown content.

    This tool automatically detects URL type and handles:
    - Sitemaps: Parses XML sitemap and returns list of URLs
    - Text/Markdown files: Directly extracts content
    - Regular webpages: Uses browser to extract content

    This is an ATOMIC tool that only extracts content. It does NOT save to storage.
    To save content, use an agent that:
    1. Calls this tool to get markdown
    2. Calls chunk_markdown to split into chunks
    3. Calls add_document to store chunks

    Args:
        url: The URL of the website to crawl (can be sitemap, txt, markdown, or webpage)
        extract_images: Whether to extract image URLs from the page
        extract_links: Whether to extract internal and external links
        word_count_threshold: Minimum word count for content blocks (filters noise)
        headless: Whether to run browser in headless mode (no visible window)
        cookies: List of cookie dicts with 'name', 'value', 'domain', etc. for authentication
        storage_state: Path to browser storage state file (for persistent sessions)
        wait_for_selector: CSS selector to wait for before extracting content
        js_code: JavaScript code to execute on the page (e.g., for scrolling)
        override_cache: Whether to bypass cache and force fresh crawl (default: False)

    Returns:
        ToolResponse containing:
        - url: the crawled URL
        - url_type: detected type ('sitemap', 'txt', 'markdown', 'webpage')
        - title: page title from metadata
        - description: page description
        - author: article author (if available)
        - published_date: publication date (if available)
        - keywords: list of keywords/tags
        - content_markdown: full markdown content
        - content_length: character count
        - images: list of extracted images (if requested)
        - links: dict of internal/external links (if requested)
        - sitemap_urls: list of URLs if url_type is 'sitemap'
        - extracted_at: ISO timestamp of extraction
    """
    try:
        # Detect URL type
        url_type = detect_url_type(url)
        
        # Handle sitemaps
        if url_type == 'sitemap':
            sitemap_urls = parse_sitemap(url)
            return ToolResponse(
                is_success=True,
                result={
                    'url': url,
                    'url_type': 'sitemap',
                    'title': f'Sitemap: {url}',
                    'description': f'Sitemap containing {len(sitemap_urls)} URLs',
                    'content_markdown': '',
                    'content_length': 0,
                    'sitemap_urls': sitemap_urls,
                    'sitemap_count': len(sitemap_urls),
                    'extracted_at': datetime.now().isoformat(),
                }
            )
        
        # For txt and markdown files, we'll still use the crawler but it should handle them
        # The crawler can handle direct file URLs
        # Configure the browser
        browser_config = BrowserConfig(
            headless=headless,
            verbose=False,
            storage_state=storage_state,
        )

        # Configure the markdown generator with content filtering
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=word_count_threshold,
            )
        )

        # Configure the crawler run
        crawler_config = CrawlerRunConfig(
            markdown_generator=markdown_generator,
            cache_mode=CacheMode.BYPASS,  # Always fetch fresh content
            wait_for=wait_for_selector if wait_for_selector else "body",
            js_code=js_code,
        )

        # Create crawler and set up authentication hook if cookies provided
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Set up authentication hook if cookies are provided
            if cookies:

                async def on_page_context_created(
                    page: Page, context: BrowserContext, **kwargs
                ):
                    """Hook to add cookies for authentication"""
                    # Add cookies to the browser context
                    await context.add_cookies(cookies)
                    return page

                # Attach the authentication hook
                crawler.crawler_strategy.set_hook(
                    "on_page_context_created", on_page_context_created
                )

            result = await crawler.arun(url=url, config=crawler_config)

            if not result.success:
                return ToolResponse(
                    is_success=False,
                    result={"url": url},
                    error=result.error_message or "Unknown error occurred",
                )

            # Extract metadata
            metadata = {}
            if hasattr(result, "metadata") and result.metadata:
                metadata = result.metadata

            # Extract markdown content
            markdown_content = ""
            markdown_length = 0
            fit_markdown = None

            if hasattr(result, "markdown"):
                if hasattr(result.markdown, "raw_markdown"):
                    markdown_content = result.markdown.raw_markdown
                    markdown_length = len(markdown_content)
                else:
                    markdown_content = result.markdown
                    markdown_length = len(markdown_content)

            if hasattr(result.markdown, "fit_markdown"):
                fit_markdown = result.markdown.fit_markdown

            # Build the response using CrawlResult dataclass
            images_list = []
            if extract_images and hasattr(result, "media") and result.media:
                if "images" in result.media:
                    for img in result.media["images"]:
                        if isinstance(img, dict):
                            images_list.append(
                                {
                                    "src": img.get("src", ""),
                                    "alt": img.get("alt", ""),
                                    "score": img.get("score", 0),
                                }
                            )

            links_dict = {"internal": [], "external": []}
            if extract_links and hasattr(result, "links") and result.links:
                links_dict = {
                    "internal": result.links.get("internal", []),
                    "external": result.links.get("external", []),
                }

            crawl_result = CrawlResult(
                url=result.url,
                title=metadata.get("title", ""),
                description=metadata.get("description", ""),
                author=metadata.get("author", ""),
                published_date=metadata.get("published_date", ""),
                keywords=metadata.get("keywords", []),
                content_markdown=markdown_content,
                content_length=markdown_length,
                images=images_list,
                links=links_dict,
            )
            
            # Add url_type to result (convert to dict and add field)
            result_dict = crawl_result.__dict__.copy()
            result_dict['url_type'] = url_type

            return ToolResponse(is_success=True, result=result_dict)

    except Exception as e:
        return ToolResponse(is_success=False, result={"url": url}, error=str(e))


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        response = await crawl_website(
            url="https://www.example.com", extract_images=True, extract_links=True
        )

        if response.is_success:
            result = response.result
            print(f"✅ Success!")
            print(f"Title: {result.title}")
            print(f"URL: {result.url}")
            print(f"Content length: {result.content_length} chars")
            print(f"Images: {len(result.images)}")
            print(f"Links: {len(result.links.get('internal', []))} internal")
        else:
            print(f"❌ Error: {response.error}")

    asyncio.run(test())
