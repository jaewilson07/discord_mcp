"""Deep crawl websites - crawl multiple pages following links.

This tool extracts raw content from multiple pages.
To save to Notion, use an agent that processes the results.
"""

from typing import Optional, List
from registry import register_command
from mcp_ce.cache.cache import cache_tool
from mcp_ce.tools.model import ToolResponse
from mcp_ce.tools.crawl4ai.models import CrawlResult, DeepCrawlResult

# Suppress Pydantic deprecation warnings from crawl4ai
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="crawl4ai")

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from urllib.parse import urlparse
import asyncio


@register_command("crawl4ai", "deep_crawl_website")
@cache_tool(ttl=7200, id_param="url")  # Cache for 2 hours
async def deep_crawl_website(
    url: str,
    max_depth: int = 3,
    max_pages: Optional[int] = None,
    include_external: bool = False,
    word_count_threshold: int = 10,
    headless: bool = True,
    url_pattern: Optional[str] = None,
    override_cache: bool = False,
) -> ToolResponse:
    """
    Deep crawl a website by following links and extracting content from multiple pages.

    This is an ATOMIC tool that only extracts content. It does NOT save to Notion.
    To save results, use an agent that processes each page result.

    Args:
        url: Starting URL to begin crawling from
        max_depth: Maximum depth to crawl (default: 3, meaning seed + 3 levels)
        max_pages: Maximum total pages to crawl (optional cap)
        include_external: Whether to follow external domain links (default: False)
        word_count_threshold: Minimum word count for content blocks (filters noise)
        headless: Whether to run browser in headless mode
        url_pattern: Optional regex pattern to filter URLs (e.g., r"/blog/|/docs/")
        override_cache: Whether to bypass cache and force fresh crawl (default: False)

    Returns:
        ToolResponse containing:
        - pages_crawled: number of pages successfully crawled
        - pages: list of page results with url, title, description, content_markdown
        - seed_url: the starting URL
        - max_depth: depth limit used
        - domain: base domain crawled

    Example:
        # Crawl bluesmuse.dance site, 3 levels deep, save to Notion
        result = await deep_crawl_website(
            url="https://www.bluesmuse.dance/blues-muse-team",
            max_depth=3,
            save_to_notion=True
        )

        print(f"Crawled {result['pages_crawled']} pages")
        for page in result['pages']:
            print(f"  - {page['url']}: {page.get('notion', {}).get('action', 'N/A')}")
    """
    try:
        # Parse the seed URL to get domain for filtering
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc

        # Build filter chain
        filters = []

        # Domain filter - only crawl same domain (unless include_external=True)
        if not include_external:
            filters.append(DomainFilter(allowed_domains=[base_domain]))

        # URL pattern filter (optional)
        if url_pattern:
            filters.append(URLPatternFilter(pattern=url_pattern))

        filter_chain = FilterChain(filters) if filters else None

        # Configure the browser
        browser_config = BrowserConfig(
            headless=headless,
            verbose=False,
        )

        # Configure markdown generator with content filtering
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=word_count_threshold,
            )
        )

        # Configure the deep crawl strategy (BFS)
        deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_depth=max_depth,
            max_pages=max_pages,
            include_external=include_external,
            filter_chain=filter_chain,
        )

        # Configure the crawler run
        crawler_config = CrawlerRunConfig(
            markdown_generator=markdown_generator,
            cache_mode=CacheMode.BYPASS,  # Always fetch fresh content
            deep_crawl_strategy=deep_crawl_strategy,
            wait_for="body",
        )

        # Collect results
        pages_results = []
        pages_crawled = 0

        # Create crawler and run deep crawl
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Use arun() for deep crawling (not arun_many)
            try:
                # arun() with deep_crawl_strategy returns a LIST of results
                results = await crawler.arun(url, config=crawler_config)

                # Results should be a list
                if not isinstance(results, list):
                    results = [results]

                print(f"\n✅ Got {len(results)} results from deep crawl\n")

            except Exception as e:
                print(f"⚠️ Crawler error: {e}")
                import traceback

                traceback.print_exc()
                results = []

            for idx, result in enumerate(results, 1):
                try:
                    if not result.success:
                        error_msg = getattr(result, "error_message", "Unknown error")
                        result_url = getattr(result, "url", "Unknown URL")
                        print(f"⚠️ Failed to crawl: {result_url} - {error_msg}")
                        continue

                    pages_crawled += 1
                    print(f"✅ Processing page {pages_crawled}: {result.url}")

                    # Extract metadata and content
                    metadata = result.metadata if hasattr(result, "metadata") else {}

                    markdown_content = ""
                    if hasattr(result, "markdown"):
                        if hasattr(result.markdown, "raw_markdown"):
                            markdown_content = result.markdown.raw_markdown
                        else:
                            markdown_content = result.markdown

                    page_result = CrawlResult(
                        url=result.url,
                        title=metadata.get("title", ""),
                        description=metadata.get("description", ""),
                        author=metadata.get("author", ""),
                        published_date=metadata.get("published_date", ""),
                        keywords=metadata.get("keywords", []),
                        content_markdown=markdown_content,
                        content_length=len(markdown_content),
                    )

                    pages_results.append(page_result)

                except Exception as e:
                    print(f"⚠️ Error processing page: {e}")
                    continue

        deep_result = DeepCrawlResult(
            seed_url=url,
            pages_crawled=pages_crawled,
            pages=pages_results,
            max_depth=max_depth,
            domain=base_domain,
        )

        return ToolResponse(is_success=True, result=deep_result)

    except Exception as e:
        return ToolResponse(
            is_success=False,
            result={
                "seed_url": url,
                "pages_crawled": 0,
                "pages": [],
            },
            error=str(e),
        )


# Example usage
if __name__ == "__main__":

    async def test():
        response = await deep_crawl_website(
            url="https://www.bluesmuse.dance/blues-muse-team",
            max_depth=2,
            max_pages=10,
        )

        if response.is_success:
            result = response.result
            print(f"\n📊 Deep Crawl Results:")
            print(f"  ✅ Success!")
            print(f"  📊 Pages crawled: {result['pages_crawled']}")
            print(f"  🌐 Domain: {result['domain']}")

            print(f"\n📄 Pages:")
            for idx, page in enumerate(result["pages"], 1):
                print(f"  {idx}. {page['url']}")
                print(f"     Title: {page['title'][:60]}...")
                print(f"     Content: {page['content_length']} chars")
        else:
            print(f"  ❌ Error: {response.error}")

    import asyncio

    asyncio.run(test())
