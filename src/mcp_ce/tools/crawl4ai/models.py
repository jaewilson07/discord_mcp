"""Crawl result models for web scraping."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from ..model import ToolResult


@dataclass
class CrawlResult(ToolResult):
    """
    Result from crawling a single web page.

    Attributes:
        url: The crawled URL
        title: Page title from metadata
        description: Page description/meta description
        author: Article author (if available)
        published_date: Publication date (if available)
        keywords: List of keywords/tags
        content_markdown: Full markdown content
        content_length: Character count of markdown content
        images: List of extracted images with src, alt, score
        links: Dict of internal/external links
        extracted_at: ISO timestamp of extraction
    """

    url: str
    title: str = ""
    description: str = ""
    author: str = ""
    published_date: str = ""
    keywords: List[str] = field(default_factory=list)
    content_markdown: str = ""
    content_length: int = 0
    images: List[Dict[str, Any]] = field(default_factory=list)
    links: Dict[str, List[Any]] = field(
        default_factory=lambda: {"internal": [], "external": []}
    )
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_article(self):
        """Convert CrawlResult to Article model for Notion export."""
        from ...models.article import Article

        return Article(
            url=self.url,
            title=self.title,
            description=self.description,
            author=self.author,
            published_date=self.published_date,
            keywords=self.keywords,
            content_markdown=self.content_markdown,
            images=self.images,
            links=self.links,
            extracted_at=self.extracted_at,
        )


@dataclass
class DeepCrawlResult(ToolResult):
    """
    Result from deep crawling multiple pages.

    Attributes:
        seed_url: The starting URL
        pages_crawled: Number of pages successfully crawled
        pages: List of CrawlResult objects for each page
        max_depth: Maximum depth crawled
        domain: Domain that was crawled
    """

    seed_url: str
    pages_crawled: int
    pages: List[CrawlResult]
    max_depth: int
    domain: str
