# Crawl4AI Agent

An intelligent web crawling and article extraction agent powered by Crawl4AI.

## Overview

The Crawl4AI Agent specializes in extracting structured content from websites and saving articles with rich metadata to local JSON files. It uses advanced web crawling techniques to handle dynamic content, JavaScript-heavy sites, and complex page structures.

## Features

- **Smart Content Extraction**: Extracts clean, structured content from any webpage
- **Metadata Collection**: Captures titles, authors, publication dates, keywords, and more
- **Image & Link Extraction**: Identifies and extracts images and links from articles
- **Local Storage**: Saves articles to JSON files with comprehensive metadata
- **Dynamic Content Support**: Handles JavaScript-heavy and dynamically loaded content
- **Content Filtering**: Removes navigation, ads, and boilerplate while preserving article content

## Tools

### CrawlWebsiteTool
Crawls websites and extracts clean, structured content including:
- Main article text in markdown format
- Page title and metadata
- Images and media elements
- Links and references
- Publication dates and authors

**Parameters:**
- `url` (required): The URL to crawl
- `extract_images` (default: True): Whether to extract image URLs
- `extract_links` (default: True): Whether to extract links
- `word_count_threshold` (default: 10): Minimum word count for content blocks
- `headless` (default: True): Run browser in headless mode

### SaveArticleTool
Saves extracted article content to a local JSON file with comprehensive metadata.

**Parameters:**
- `url` (required): The article URL
- `title` (required): Article title
- `content` (required): Main content in markdown
- `description` (optional): Article summary
- `author` (optional): Article author
- `published_date` (optional): Publication date
- `keywords` (optional): List of keywords/tags
- `images` (optional): List of images with URLs and alt text
- `links` (optional): Dictionary of internal/external links
- `custom_filename` (optional): Custom filename for the saved article

## Usage Example

```python
from agency_swarm import Agency
from crawl4ai_agent import crawl4ai_agent

# Create an agency with the Crawl4AI agent
agency = Agency([
    crawl4ai_agent
])

# Example: Extract an article
result = agency.run("Extract the article from https://example.com/blog/post")
```

## Installation

The agent requires Crawl4AI to be installed:

```bash
pip install crawl4ai>=0.3.74
```

After installation, run the Crawl4AI setup:

```bash
crawl4ai-setup
```

## Output Format

Articles are saved as JSON files in the `files/` folder with the following structure:

```json
{
  "id": "unique-id",
  "url": "https://example.com/article",
  "title": "Article Title",
  "description": "Article description",
  "author": "Author Name",
  "published_date": "2024-01-01",
  "keywords": ["keyword1", "keyword2"],
  "content": "# Article content in markdown...",
  "content_length": 5000,
  "images": [
    {
      "src": "https://example.com/image.jpg",
      "alt": "Image description",
      "score": 0.9
    }
  ],
  "links": {
    "internal": ["https://example.com/page1"],
    "external": ["https://other-site.com"]
  },
  "metadata": {
    "extracted_at": "2024-11-14T10:30:00",
    "saved_at": "2024-11-14T10:30:05",
    "file_version": "1.0"
  }
}
```

## Agent Workflow

1. **Receive URL**: User provides a URL to crawl
2. **Crawl Website**: CrawlWebsiteTool extracts content and metadata
3. **Validate Content**: Check extraction quality and completeness
4. **Save Article**: SaveArticleTool persists the article to JSON
5. **Confirm Success**: Report extraction details to user

## Best Practices

- Always verify URLs are accessible before crawling
- Use descriptive filenames or let the tool generate them from titles
- Extract comprehensive metadata when available
- Handle errors gracefully with clear error messages
- Respect robots.txt and crawling best practices
- Be mindful of rate limiting when crawling multiple pages
