# Multi-Site Web Spider Architecture & Design Decisions

## Overview

This document describes the architecture, design decisions, and implementation patterns for our multi-site web spider system. The spider extracts content from fundamentally different sites (YouTube, Twitter/X, Reddit, Depop, imageboards, forums, WordPress blogs) while maintaining code maintainability, extensibility, and resilience.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Design Principles](#core-design-principles)
3. [Current Implementation](#current-implementation)
4. [Proposed Architecture Pattern](#proposed-architecture-pattern)
5. [Scientific Dataset Generation](#scientific-dataset-generation)
6. [Design Decisions](#design-decisions)
7. [User Stories](#user-stories)
8. [Future Enhancements](#future-enhancements)

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Site Spider                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Reddit     │  │   YouTube    │  │    Depop     │      │
│  │  Extractor   │  │  Extractor   │  │  Extractor   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │                │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │  Base Extractor │                         │
│                  │   (Abstract)    │                         │
│                  └────────┬────────┘                         │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │  Factory        │                         │
│                  │  Registry       │                         │
│                  └────────┬────────┘                         │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │  Configuration  │                         │
│                  │  (YAML/JSON)    │                         │
│                  └─────────────────┘                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Pydantic│  │  Storage │  │ Dedupe   │  │  Quality │  │
│  │ Validation│ │  (Neo4j) │  │ (Valkey) │  │  Scorer  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Scientific Dataset Generation                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Policy  │  │   WARC   │  │  History │  │ Snapshot │  │
│  │  Engine  │  │  Storage │  │ Tracking │  │Versioning│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Separation of Concerns

Each site's parsing logic is isolated in its own extractor class. This ensures that:
- Changes to one site's HTML structure don't affect others
- Each extractor can be independently tested
- Site-specific quirks are contained

### 2. Adapter Pattern

Site-specific extractors adapt the unique structure of each platform to a common interface (`BaseSiteExtractor`). This allows the core spider to work with any site without knowing implementation details.

### 3. Configuration-Driven Selectors

CSS selectors and XPath expressions live in YAML configuration files, not in code. This enables:
- Quick updates when sites change their HTML
- Version-controlled selector changes
- Easy rollback of broken selectors
- Non-developer maintenance

### 4. Type Safety with Pydantic

Each site's data schema is defined using Pydantic models, providing:
- Automatic validation of extracted data
- Type hints for better IDE support
- Clear error messages when data doesn't match expected structure
- Documentation of expected fields

### 5. Factory Pattern for Dynamic Selection

A registry-based factory selects the appropriate extractor at runtime based on the URL being scraped. This allows:
- Adding new sites without modifying core code
- Runtime site detection
- Plugin-like extensibility

## Current Implementation

### Existing Structure

Our current implementation follows a similar pattern but is more focused on image crawling:

```
src/image_crawler/
├── platforms/
│   ├── base.py              # BasePlatformCrawler (abstract)
│   ├── reddit.py            # RedditCrawler
│   └── instagram.py         # InstagramCrawler
├── orchestrator.py          # MasterCrawler
├── frontier.py              # URL queue management
├── fetch_worker.py          # Worker threads
├── storage.py               # Neo4j storage
├── deduplication.py         # Duplicate detection
└── quality_scorer.py        # Image quality scoring
```

### Current Base Class

```python
class BasePlatformCrawler(ABC):
    """Base class for platform-specific crawlers."""
    
    @abstractmethod
    def fetch_image_urls(self, limit: int = 50) -> List[str]:
        """Fetch image URLs from platform."""
        pass
    
    @abstractmethod
    def get_source_metadata(self) -> Dict:
        """Get source metadata."""
        pass
```

### Strengths of Current Implementation

1. **Clear abstraction**: Base class enforces consistent interface
2. **Platform isolation**: Each platform has its own crawler
3. **Orchestration**: MasterCrawler coordinates multiple platforms
4. **Deduplication**: Built-in duplicate detection
5. **Quality scoring**: Automatic quality assessment

### Areas for Enhancement

1. **Selector configuration**: Currently hardcoded in extractors
2. **Validation**: No structured validation of extracted data
3. **Fallback selectors**: No graceful degradation when selectors break
4. **Schema definitions**: No explicit data schemas
5. **Registry pattern**: Manual crawler registration

## Proposed Architecture Pattern

### Directory Structure

```
spider/
├── core/
│   ├── base.py              # Abstract extractor interface
│   ├── registry.py          # Site handler factory
│   └── models.py            # Pydantic schemas
├── extractors/
│   ├── reddit.py
│   ├── youtube.py
│   ├── depop.py
│   ├── imageboard.py
│   ├── wordpress.py
│   └── twitter.py
├── config/
│   ├── sites.yaml           # Site profiles + selectors
│   └── schemas.json         # Output schemas
└── utils/
    ├── dom.py               # Shared DOM utilities
    └── validators.py        # Common validation logic
```

### Abstract Base Extractor

```python
# core/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass

@dataclass
class ScrapeConfig:
    """Site-specific configuration"""
    site_name: str
    base_selectors: Dict[str, str]
    nested_selectors: Dict[str, Dict[str, str]]
    fallback_selectors: Dict[str, list[str]]

class BaseSiteExtractor(ABC):
    """Abstract extractor for any site"""
    
    def __init__(self, config: ScrapeConfig):
        self.config = config
        self.site_name = config.site_name
    
    @abstractmethod
    def extract(self, html: str) -> Dict[str, Any]:
        """Extract structured data from HTML"""
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data"""
        pass
```

### Site-Specific Extractor with Pydantic

```python
# extractors/reddit.py
from pydantic import BaseModel, Field, validator
from ..core.base import BaseSiteExtractor, ScrapeConfig

class RedditPost(BaseModel):
    """Schema for Reddit posts"""
    title: str = Field(..., description="Post title")
    author: str = Field(..., description="Author username")
    subreddit: str = Field(..., description="Subreddit name")
    score: int = Field(default=0, description="Upvote count")
    url: str = Field(..., description="Post URL")
    created_utc: Optional[int] = Field(None, description="Unix timestamp")
    
    @validator('author')
    def validate_author(cls, v):
        if v.startswith('[deleted]'):
            raise ValueError("Deleted post")
        return v

@register_extractor("reddit")
class RedditExtractor(BaseSiteExtractor):
    def __init__(self, config: ScrapeConfig):
        super().__init__(config)
        self.schema = RedditPost
    
    def extract(self, html: str) -> dict:
        # Implementation with fallback selectors
        pass
    
    def validate(self, data: dict) -> bool:
        try:
            post = RedditPost(**data)
            return True
        except ValueError as e:
            return False
```

### Factory Registry

```python
# core/registry.py
from typing import Dict, Type
import yaml

EXTRACTORS: Dict[str, Type[BaseSiteExtractor]] = {}

def register_extractor(site_name: str):
    """Decorator to register site extractors"""
    def decorator(cls):
        EXTRACTORS[site_name] = cls
        return cls
    return decorator

class ExtractorFactory:
    @staticmethod
    def load_config(config_file: str = "config/sites.yaml"):
        """Load all site configurations"""
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def get_extractor(site_name: str, config: ScrapeConfig):
        """Get extractor instance for a site"""
        if site_name not in EXTRACTORS:
            raise ValueError(f"No extractor registered for {site_name}")
        extractor_class = EXTRACTORS[site_name]
        return extractor_class(config)
```

### Configuration File

```yaml
# config/sites.yaml
sites:
  reddit:
    base_url: "reddit.com"
    selectors:
      title: "[data-testid='post-title']"
      author: "[data-testid='post-author-name']"
      score: "[data-testid='vote-button-up']"
    fallback_selectors:
      title:
        - "h3.Post__Title"
        - "div.PostHeader__post-title"
    nested_selectors:
      comments:
        container: "div[data-testid='comment']"
        author: "a[data-testid='comment-author']"
  
  youtube:
    base_url: "youtube.com"
    selectors:
      title: "yt-formatted-string[role='heading']"
      author: "ytd-channel-name a"
    fallback_selectors:
      title:
        - "h1.style-scope.ytd-video-primary-info-renderer"
```

## Design Decisions

### Decision 1: Abstract Base Class vs. Protocol

**Decision**: Use ABC (Abstract Base Class) with `@abstractmethod`

**Rationale**:
- Enforces interface at class definition time
- Clear inheritance hierarchy
- Better IDE support and type checking
- Explicit contract for implementers

**Alternatives Considered**:
- Protocol (structural subtyping): More flexible but less explicit
- Duck typing: Too loose, no compile-time guarantees

### Decision 2: Configuration in YAML vs. Code

**Decision**: Store selectors in YAML configuration files

**Rationale**:
- Sites change HTML frequently; YAML allows quick updates without code changes
- Version control tracks selector evolution
- Non-developers can update selectors
- Easy rollback when selectors break
- Separates "what to extract" from "how to extract"

**Trade-offs**:
- Slightly more complex initial setup
- Requires YAML parsing dependency
- Need to validate configuration at runtime

### Decision 3: Pydantic for Validation

**Decision**: Use Pydantic models for data validation

**Rationale**:
- Automatic type coercion and validation
- Clear error messages
- Self-documenting schemas
- Integration with FastAPI if needed
- Runtime type checking

**Alternatives Considered**:
- Manual validation: Too error-prone
- JSON Schema: More verbose, less Pythonic
- Dataclasses: No built-in validation

### Decision 4: Factory Pattern with Decorator Registry

**Decision**: Use decorator-based registry for extractor registration

**Rationale**:
- Clean, declarative registration
- Automatic discovery when modules are imported
- No manual registration code needed
- Easy to extend with new sites

**Implementation**:
```python
@register_extractor("reddit")
class RedditExtractor(BaseSiteExtractor):
    # Implementation
```

### Decision 5: Fallback Selectors

**Decision**: Support multiple selector fallbacks per field

**Rationale**:
- Sites frequently change HTML structure
- Graceful degradation prevents complete failures
- Supports A/B testing by sites
- Historical selector support for older pages

**Implementation**:
```python
def _get_with_fallbacks(self, soup, primary, fallbacks):
    elem = soup.select_one(primary)
    if elem:
        return elem.get_text(strip=True)
    for fallback in fallbacks:
        elem = soup.select_one(fallback)
        if elem:
            return elem.get_text(strip=True)
    return ""
```

### Decision 6: Site Detection Strategy

**Decision**: URL-based site detection using base_url matching

**Rationale**:
- Simple and fast
- Works for most cases
- Can be extended with regex patterns if needed

**Implementation**:
```python
def _detect_site(self, url: str) -> str:
    for site, config in self.site_configs['sites'].items():
        if config['base_url'] in url:
            return site
    return None
```

### Decision 7: Separation of Extraction and Validation

**Decision**: Separate `extract()` and `validate()` methods

**Rationale**:
- Allows extraction to return raw data
- Validation can be optional or conditional
- Easier to debug extraction issues
- Can extract without validating if needed

**Trade-offs**:
- Two-step process (but can be combined in wrapper)

### Decision 8: Nested Selectors for Complex Structures

**Decision**: Support nested selector configuration for complex data structures

**Rationale**:
- Comments, replies, and nested content need structured extraction
- Keeps configuration declarative
- Supports recursive structures

**Example**:
```yaml
nested_selectors:
  comments:
    container: "div[data-testid='comment']"
    author: "a[data-testid='comment-author']"
    text: "div[data-testid='comment-text']"
    replies:
      container: "div.reply"
      author: "a.reply-author"
```

## Scientific Dataset Generation

For scientific research and reproducible ML training, the spider includes comprehensive dataset generation features inspired by Internet Archive's WARC format and Common Crawl practices. This ensures full reproducibility, audit trails, and policy compliance.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│              Scientific Spider Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  URL Request → Policy Check → Rate Limit → Fetch             │
│       │              │            │          │                │
│       │              │            │          ▼                │
│       │              │            │    ┌──────────┐         │
│       │              │            │    │  HTTP    │         │
│       │              │            │    │ Response │         │
│       │              │            │    └────┬─────┘         │
│       │              │            │         │                │
│       │              │            │         ▼                │
│       │              │            │    Content Hash          │
│       │              │            │    (SHA256)               │
│       │              │            │         │                │
│       │              │            │         ▼                │
│       │              │            │    Change Detection      │
│       │              │            │         │                │
│       │              │            │         ▼                │
│       │              │            │    ┌──────────┐         │
│       │              │            │    │   WARC   │         │
│       │              │            │    │ Snapshot │         │
│       │              │            │    └────┬─────┘         │
│       │              │            │         │                │
│       │              │            │         ▼                │
│       │              │            │    Extract Data         │
│       │              │            │    (Pydantic)             │
│       │              │            │         │                │
│       │              │            │         ▼                │
│       │              │            │    ┌──────────┐         │
│       │              │            │    │ Parquet  │         │
│       │              │            │    │ Storage  │         │
│       │              │            │    └────┬─────┘         │
│       │              │            │         │                │
│       │              │            └─────────┼────────────────┘
│       │              │                      │                  │
│       └──────────────┼──────────────────────┘                  │
│                      │                                         │
│                      ▼                                         │
│              ┌──────────────┐                                  │
│              │   History    │                                  │
│              │   Ledger     │                                  │
│              │  (Parquet)   │                                  │
│              └──────────────┘                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Core Dataset Policies

The policy engine enforces per-site and global crawling rules to prevent abuse and ensure reproducibility.

```python
# core/policies.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
import hashlib

@dataclass
class CrawlPolicy:
    """Per-site crawling rules"""
    min_delay: int = 300  # seconds between requests
    max_requests_per_hour: int = 60
    respect_robots_txt: bool = True
    user_agent: str = "ScientificSpider/1.0 (contact@example.com)"
    snapshot_retention_days: int = 90
    change_threshold: float = 0.1  # Re-crawl if >10% content changed
    
    # Site-specific overrides
    @classmethod
    def from_site(cls, site_name: str) -> 'CrawlPolicy':
        defaults = {
            'youtube': {'min_delay': 600, 'max_requests_per_hour': 30},
            'twitter': {'min_delay': 900, 'max_requests_per_hour': 20},
            'reddit': {'min_delay': 120, 'max_requests_per_hour': 120},
        }
        return cls(**defaults.get(site_name, {}))

@dataclass
class CrawlHistory:
    """Immutable record of every crawl attempt"""
    url: str
    crawl_id: str  # UUID or hash
    timestamp: datetime
    status_code: Optional[int]
    content_hash: Optional[str]  # SHA256 of raw HTML
    content_length: Optional[int]
    extractor_version: str  # Git commit hash
    policy_version: str
    raw_content_path: str  # S3/blob path to WARC
    extracted_data_path: str  # Parquet/JSONL path
    success: bool
    error: Optional[str]
    change_score: Optional[float]  # vs previous snapshot
```

### Snapshot Storage Architecture

Raw HTML is stored in WARC (Web ARChive) format for reproducibility, while extracted data is stored as Parquet for efficient analysis.

```
dataset/
├── snapshots/2025-12-24/
│   ├── reddit-r-all-abc123.warc.gz     # Raw HTML archive
│   └── extracted/
│       ├── reddit-posts.parquet        # Structured data
│       └── reddit-posts.jsonl.gz       # Raw JSONL backup
├── history/
│   └── crawl_history.parquet           # All crawl metadata
└── policies/
    └── site_policies.yaml              # Active policies
```

### Enhanced Scientific Spider

The `ScientificSpider` integrates seamlessly with the extractor architecture:

```python
# core/spider.py
import warcio  # WARC format
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path
from urllib.parse import urlparse
import time
import hashlib
from .policies import CrawlPolicy, CrawlHistory
from .registry import ExtractorFactory

class ScientificSpider:
    
    def __init__(self, dataset_root: Path, policy_file: str = "config/policies.yaml"):
        self.dataset_root = dataset_root
        self.history_table = self._load_history()
        self.factory = ExtractorFactory()
    
    def should_crawl(self, url: str) -> bool:
        """Scientific decision: policy + freshness + change detection"""
        site_name = self._detect_site(url)
        policy = CrawlPolicy.from_site(site_name)
        
        # Check rate limiting
        recent_crawls = self._recent_crawls(url, policy.max_requests_per_hour)
        if len(recent_crawls) >= policy.max_requests_per_hour:
            return False
        
        # Check freshness (Internet Archive-style)
        last_crawl = self._last_successful_crawl(url)
        if last_crawl and (datetime.now() - last_crawl.timestamp) < timedelta(hours=24):
            return False
        
        return True
    
    def crawl(self, url: str) -> CrawlHistory:
        """Full pipeline: policy check → fetch → snapshot → extract → validate"""
        site_name = self._detect_site(url)
        policy = CrawlPolicy.from_site(site_name)
        
        # Rate limiting
        time.sleep(policy.min_delay)
        
        crawl_id = hashlib.sha256(f"{url}{time.time()}".encode()).hexdigest()[:8]
        history = CrawlHistory(
            url=url, crawl_id=crawl_id, timestamp=datetime.now(),
            status_code=None, content_hash=None, success=False
        )
        
        try:
            # Fetch with policy headers
            response = requests.get(
                url, headers={'User-Agent': policy.user_agent},
                timeout=30
            )
            history.status_code = response.status_code
            
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}")
            
            # Compute content hash for deduplication
            content_hash = hashlib.sha256(response.content).hexdigest()
            history.content_hash = content_hash
            history.content_length = len(response.content)
            
            # Check if identical to last snapshot
            if self._content_unchanged(url, content_hash):
                history.error = "No change detected"
                return self._save_history(history)
            
            # Save raw snapshot as WARC
            raw_path = self._save_warc_snapshot(url, response)
            history.raw_content_path = str(raw_path)
            
            # Extract structured data
            config = self._get_site_config(site_name)
            extractor = self.factory.get_extractor(site_name, config)
            extracted = extractor.extract(response.text)
            
            if not extractor.validate(extracted):
                raise ValueError("Extraction validation failed")
            
            # Save extracted data
            data_path = self._save_extracted_data(site_name, extracted)
            history.extracted_data_path = str(data_path)
            history.success = True
            
            # Compute change score vs previous
            history.change_score = self._compute_change_score(url, response.content)
            
        except Exception as e:
            history.error = str(e)
        
        return self._save_history(history)
    
    def _save_warc_snapshot(self, url: str, response) -> Path:
        """Save raw HTML as Internet Archive-compatible WARC"""
        snapshot_dir = self.dataset_root / "snapshots" / self._today_str()
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        warc_path = snapshot_dir / f"{self._site_from_url(url)}-{uuid.uuid4().hex}.warc.gz"
        
        with warcio.WARCWriter(str(warc_path), gzip=True) as writer:
            writer.write_record(
                url, 'response',
                response.content,
                headers={'Content-Type': 'text/html'}
            )
        return warc_path
    
    def _save_extracted_data(self, site_name: str, data: dict) -> Path:
        """Append to site-specific Parquet dataset"""
        snapshot_dir = self.dataset_root / "snapshots" / self._today_str() / "extracted"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        parquet_path = snapshot_dir / f"{site_name}-posts.parquet"
        
        # Convert to Arrow table and append
        table = pa.Table.from_pydict({k: [v] for k, v in data.items()})
        
        if parquet_path.exists():
            existing = pq.read_table(parquet_path)
            table = pa.concat_tables([existing, table])
        
        pq.write_table(table, parquet_path)
        return parquet_path
    
    def dataset_summary(self) -> Dict:
        """Scientific overview: coverage, freshness, quality metrics"""
        return {
            'total_crawls': len(self.history_table),
            'success_rate': self._success_rate(),
            'coverage_by_site': self._coverage_by_site(),
            'freshness_24h': self._count_recent_successful(timedelta(hours=24)),
            'total_raw_gb': self._total_raw_size(),
            'total_records': self._total_extracted_records()
        }
```

### Reproducibility Features

#### 1. WARC Snapshots (Internet Archive Standard)

- Every raw HTML response archived in WARC format
- Exact reproducibility: re-extract with new parsers against old snapshots
- Content deduplication via SHA256 hashes
- Standard format compatible with web archive tools

#### 2. Immutable History Ledger

All crawl attempts are recorded in a Parquet history table:

```python
# Query examples
recent_failures = spider.history_table.filter(
    pl.col("success") == False
).select("url", "error", "timestamp")

site_coverage = spider.history_table.group_by("site").agg(
    success_rate=pl.col("success").mean()
)
```

#### 3. Policy Enforcement

- Automatic robots.txt respect
- Configurable rate limits per site
- User-agent identifies scientific purpose
- Batch scheduling avoids slamming servers
- Per-site delay configuration

#### 4. Change Detection

- Only re-crawl if content changed >10% (configurable threshold)
- Diff scores track site evolution over time
- Snapshot rollback for extractor fixes
- Content hash comparison for exact duplicates

### Usage Workflow

```python
from pathlib import Path
from core.spider import ScientificSpider

# Initialize with dataset root
spider = ScientificSpider(dataset_root=Path("datasets/science-v1"))

# Policy-driven crawling
if spider.should_crawl("https://reddit.com/r/all"):
    history = spider.crawl("https://reddit.com/r/all")
    print(f"Crawl {history.crawl_id}: {'Success' if history.success else 'Failed'}")

# Scientific analysis
summary = spider.dataset_summary()
print(f"Total crawls: {summary['total_crawls']}")
print(f"Success rate: {summary['success_rate']:.2%}")
print(f"Coverage by site: {summary['coverage_by_site']}")
```

### Integration with Existing Architecture

The scientific dataset features integrate seamlessly:

1. **Extractors**: Use existing `BaseSiteExtractor` implementations
2. **Factory**: `ExtractorFactory` selects appropriate extractor
3. **Configuration**: Site policies extend existing YAML configs
4. **Storage**: WARC for raw, Parquet for extracted (complements Neo4j)
5. **History**: Immutable audit trail for all operations

### Benefits for Scientific Research

1. **Reproducibility**: Exact snapshots allow re-extraction with improved parsers
2. **Auditability**: Complete history of every crawl attempt
3. **Citation**: Each extracted record can reference exact source snapshot
4. **Compliance**: Policy enforcement ensures ethical crawling
5. **Efficiency**: Change detection avoids redundant crawls
6. **Quality**: Validation ensures data integrity at every step

## User Stories

See [USER_STORIES_SWIFTIES.md](./USER_STORIES_SWIFTIES.md) for detailed user stories. Key stories include:

- **US-001**: Track content across multiple Reddit sources
- **US-002**: Tag posts by era/category
- **US-003**: Automatic content discovery
- **US-004**: Cross-platform content aggregation
- **US-005**: Era-based content browsing

### Architecture Support for User Stories

| User Story | Architecture Support |
|------------|---------------------|
| US-001: Multiple Reddit Sources | Multiple `RedditExtractor` instances with different subreddit configs |
| US-002: Era Tagging | Pydantic schema includes `era` field; extractor can detect from content |
| US-003: Auto Discovery | Platform crawlers poll at intervals; new content triggers extraction |
| US-004: Cross-Platform | Factory pattern allows multiple extractors; unified storage in Neo4j |
| US-005: Era Browsing | Graph queries filter by era property; extractor sets era during extraction |

## Key Benefits

### Maintainability

When a site changes its HTML structure:
1. Update YAML config with new selectors
2. Test with sample HTML
3. Deploy configuration change
4. No code changes required

### Testability

Each extractor is independently testable:
```python
def test_reddit_extractor():
    extractor = RedditExtractor(config)
    html = load_test_html("reddit_post.html")
    data = extractor.extract(html)
    assert extractor.validate(data)
```

### Extensibility

Adding a new site requires:
1. Create new extractor file implementing `BaseSiteExtractor`
2. Add `@register_extractor("sitename")` decorator
3. Add YAML config entry
4. Core spider code unchanged

### Resilience

- Fallback selectors prevent complete failures
- Pydantic validation catches data quality issues early
- Graceful error handling per site
- Configuration can be rolled back easily

### Configuration Drift Prevention

- Selectors in version-controlled YAML
- Changes are auditable
- Easy to revert broken selectors
- Can track selector evolution over time

## Future Enhancements

### 1. Machine Learning for Selector Discovery

Use ML to automatically discover selectors when sites change:
- Train model on successful extractions
- Auto-suggest new selectors when old ones break
- Learn from manual corrections

### 2. Selector Health Monitoring

Track selector success rates:
- Alert when success rate drops
- Auto-enable fallback selectors
- Historical performance tracking

### 3. Multi-Format Support

Extend beyond HTML:
- JSON API responses
- GraphQL queries
- RSS/Atom feeds
- JavaScript-rendered content (Selenium/Playwright)

### 4. Rate Limiting and Politeness

Per-site rate limiting:
- Respect robots.txt
- Configurable delays
- Exponential backoff on errors
- Site-specific politeness policies

### 5. Caching and Incremental Updates

Smart caching:
- Cache extracted data
- Incremental updates only
- Change detection
- Efficient re-crawling

### 6. Parallel Extraction

Concurrent processing:
- Multiple workers per site
- Async/await support
- Connection pooling
- Resource management

## Migration Path

### Phase 1: Enhance Current Implementation

1. Add Pydantic schemas to existing extractors
2. Extract selectors to configuration files
3. Add fallback selector support
4. Implement factory registry

### Phase 2: Unified Architecture

1. Create new `spider/` directory structure
2. Migrate existing extractors to new pattern
3. Add new site extractors (YouTube, Twitter, etc.)
4. Update MasterCrawler to use factory

### Phase 3: Advanced Features

1. ML-based selector discovery
2. Health monitoring
3. Multi-format support
4. Enhanced caching

## References

- [Scrapy Architecture](https://docs.scrapy.org/en/latest/topics/architecture.html) - Proven patterns for web scraping
- [Pydantic Documentation](https://docs.pydantic.dev/) - Data validation framework
- [Adapter Pattern](https://refactoring.guru/design-patterns/adapter) - Design pattern reference
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method) - Design pattern reference

## Conclusion

This architecture provides a solid foundation for a multi-site web spider that can scale to 20+ sites while maintaining code quality and developer productivity. The separation of concerns, configuration-driven approach, and type safety ensure that the system remains maintainable as it grows.

