# Refactoring Guidelines

This document provides guidelines for refactoring code in this repository, addressing the layout problems and establishing best practices for maintaining a clean, organized codebase.

## Table of Contents

1. [Repository Layout Principles](#repository-layout-principles)
2. [Refactoring Process](#refactoring-process)
3. [Code Organization Standards](#code-organization-standards)
4. [Migration Strategies](#migration-strategies)
5. [Common Refactoring Patterns](#common-refactoring-patterns)

## Repository Layout Principles

### Current Problems

The repository has suffered from several layout issues:

1. **Top-level script proliferation**: Many utility scripts (`check_*.py`, `crawl_*.py`, `download_*.py`) clutter the root directory
2. **Inconsistent module organization**: Related functionality scattered across different directories
3. **Mixed concerns**: Scripts, libraries, notebooks, and documentation intermingled
4. **Unclear boundaries**: Unclear separation between production code, utilities, and experiments

### Target Structure

```
jupyter/
├── src/                          # Production code (installable packages)
│   ├── feed/                     # Feed/crawler system
│   ├── image_dedup/              # Image deduplication
│   ├── image_captioning/          # Image captioning
│   ├── providers/                # External service providers (ASR, VLM, etc.)
│   └── ...
├── scripts/                      # Utility scripts (not installable)
│   ├── monitoring/               # Status checks, health monitoring
│   ├── crawling/                 # Crawler utilities
│   ├── data_processing/          # Data transformation scripts
│   ├── deployment/               # Deployment automation
│   └── archive/               # Deprecated/archived scripts
├── notebooks/                    # Jupyter notebooks
│   ├── examples/                 # Example workflows
│   ├── experiments/              # Experimental work
│   └── runpod_deployments/       # RunPod deployment notebooks
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── docs/                         # Documentation
│   ├── architecture/             # Architecture decisions
│   ├── guides/                   # User guides
│   └── api/                      # API documentation
├── agents/                       # Agent implementations
├── media-platform/               # Media platform application
├── config/                       # Configuration files
├── data/                         # Data files (git-ignored or LFS)
└── docker/                       # Docker-related files
```

### Key Principles

1. **Separation of Concerns**
   - Production code in `src/` (installable packages)
   - Utility scripts in `scripts/` (organized by function)
   - Experiments in `notebooks/experiments/`
   - Documentation in `docs/`

2. **Module Cohesion**
   - Related functionality grouped together
   - Clear module boundaries
   - Minimal cross-module dependencies

3. **Discoverability**
   - Clear naming conventions
   - Logical directory structure
   - README files in each major directory

4. **Maintainability**
   - Easy to find code
   - Easy to understand relationships
   - Easy to add new features

## Refactoring Process

### Before Refactoring

1. **Identify the Scope**
   - What code/files are affected?
   - What are the dependencies?
   - What tests exist?

2. **Create a Plan**
   - Document current state
   - Define target state
   - List migration steps
   - Identify risks

3. **Get Approval** (for large refactors)
   - Create an issue or ADR
   - Get team review
   - Document the approach

### During Refactoring

1. **Work Incrementally**
   - Make small, testable changes
   - Keep tests passing
   - Commit frequently with clear messages

2. **Maintain Functionality**
   - Don't change behavior (unless that's the goal)
   - Update imports/exports carefully
   - Test after each change

3. **Update Documentation**
   - Update README files
   - Update import paths in docs
   - Update architecture diagrams

### After Refactoring

1. **Verify Everything Works**
   - Run full test suite
   - Check all imports
   - Verify scripts still work

2. **Clean Up**
   - Remove deprecated code
   - Update .gitignore if needed
   - Archive old files

3. **Document Changes**
   - Update CHANGELOG
   - Update migration guide if needed
   - Announce breaking changes

## Code Organization Standards

### Module Structure

Each module in `src/` should follow this structure:

```
module_name/
├── __init__.py           # Public API exports
├── core.py               # Core functionality
├── models.py             # Data models (if applicable)
├── utils.py              # Utility functions
├── README.md             # Module documentation
└── tests/                # Module-specific tests (optional)
    └── test_core.py
```

### Script Organization

Scripts in `scripts/` should be organized by function:

```
scripts/
├── monitoring/
│   ├── check_neo4j_status.py
│   ├── check_runpod_pod_logs.py
│   └── monitor_crawlers.sh
├── crawling/
│   ├── crawl_reddit_subreddit.py
│   └── fast_thread_crawler.py
└── data_processing/
    ├── download_all_thread_images.py
    └── organize_imageboard_images.py
```

### Naming Conventions

- **Modules**: `snake_case` (e.g., `image_dedup`, `feed_crawler`)
- **Classes**: `PascalCase` (e.g., `ProductStorage`, `DepopAdapter`)
- **Functions**: `snake_case` (e.g., `get_connection`, `store_product`)
- **Scripts**: `snake_case` with verb prefix (e.g., `check_status.py`, `crawl_reddit.py`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)

### Import Organization

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import neo4j
import requests

# Local
from src.feed.storage.neo4j_connection import get_connection
from src.feed.platforms.depop import DepopAdapter
```

## Migration Strategies

### Moving Top-Level Scripts

When moving scripts from root to `scripts/`:

1. **Create target directory** if it doesn't exist
2. **Move the file** with git: `git mv check_neo4j_status.py scripts/monitoring/`
3. **Update imports** in the moved file
4. **Update references** in other files
5. **Update documentation** that references the script
6. **Test the script** in its new location

### Consolidating Related Code

When consolidating scattered functionality:

1. **Identify all related files**
2. **Create target module** in `src/`
3. **Move files incrementally**
4. **Refactor to shared interfaces**
5. **Update all imports**
6. **Remove old files**

### Deprecating Old Code

When deprecating code:

1. **Add deprecation warnings**
2. **Document migration path**
3. **Set removal date** (e.g., "Will be removed in v2.0")
4. **Move to `scripts/archive/`** when ready
5. **Update documentation**

## Common Refactoring Patterns

### Pattern 1: Extract Utility Functions

**Before:**
```python
# check_neo4j_status.py
def check_status():
    driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", ...)
    # ... check logic
```

**After:**
```python
# src/feed/storage/neo4j_connection.py
def get_connection():
    # ... connection logic
    return driver

# scripts/monitoring/check_neo4j_status.py
from src.feed.storage.neo4j_connection import get_connection

def check_status():
    driver = get_connection()
    # ... check logic
```

### Pattern 2: Organize Platform Adapters

**Before:**
```
crawl_depop.py
crawl_reddit.py
crawl_fapello.py
```

**After:**
```
src/feed/platforms/
├── __init__.py
├── base.py              # Base adapter interface
├── depop.py
├── reddit.py
└── fapello.py

scripts/crawling/
├── crawl_depop.py      # CLI script using adapter
├── crawl_reddit.py
└── crawl_fapello.py
```

### Pattern 3: Consolidate Check Scripts

**Before:**
```
check_neo4j_status.py
check_runpod_pod_logs.py
check_reddit_post.py
```

**After:**
```
scripts/monitoring/
├── __init__.py
├── neo4j.py            # check_neo4j_status functionality
├── runpod.py          # check_runpod_pod_logs functionality
└── reddit.py          # check_reddit_post functionality

scripts/monitoring/cli.py  # Unified CLI entry point
```

### Pattern 4: Separate Concerns

**Before:**
```python
# crawl_reddit.py (does everything)
def crawl():
    # Fetch data
    # Parse HTML
    # Store in Neo4j
    # Send notifications
```

**After:**
```python
# src/feed/platforms/reddit.py (data fetching)
class RedditAdapter:
    def fetch_post(self, url): ...

# src/feed/storage/thread_storage.py (storage)
class ThreadStorage:
    def store_thread(self, thread): ...

# scripts/crawling/crawl_reddit.py (orchestration)
def crawl():
    adapter = RedditAdapter()
    storage = ThreadStorage()
    # ... orchestration
```

## Refactoring Checklist

Before submitting a refactoring PR:

- [ ] All tests pass
- [ ] No functionality changed (unless intentional)
- [ ] Imports updated throughout codebase
- [ ] Documentation updated
- [ ] README files updated
- [ ] Migration path documented (if breaking)
- [ ] Deprecated code marked (if applicable)
- [ ] Git history preserved (using `git mv`)
- [ ] Code follows style guidelines
- [ ] No secrets or sensitive data exposed

## Examples

### Example 1: Moving a Check Script

```bash
# 1. Create target directory
mkdir -p scripts/monitoring

# 2. Move file with git
git mv check_neo4j_status.py scripts/monitoring/check_neo4j_status.py

# 3. Update imports in the file
# Change: from feed.storage import ...
# To: from src.feed.storage import ...

# 4. Update any references
grep -r "check_neo4j_status" . --exclude-dir=.git

# 5. Test
python scripts/monitoring/check_neo4j_status.py
```

### Example 2: Consolidating Crawlers

```bash
# 1. Create module structure
mkdir -p src/feed/crawler/reddit

# 2. Move and refactor files
git mv crawl_reddit_json.py src/feed/crawler/reddit/json_crawler.py
git mv crawl_reddit_rss.py src/feed/crawler/reddit/rss_crawler.py

# 3. Create unified interface
# src/feed/crawler/reddit/__init__.py
from .json_crawler import JsonCrawler
from .rss_crawler import RssCrawler

# 4. Update scripts to use new interface
# scripts/crawling/crawl_reddit.py
from src.feed.crawler.reddit import JsonCrawler, RssCrawler
```

## Anti-Patterns to Avoid

1. **Don't create deep nesting** - Keep directory depth reasonable (max 4-5 levels)
2. **Don't mix concerns** - Keep scripts, libraries, and tests separate
3. **Don't break without migration** - Provide migration paths for breaking changes
4. **Don't refactor everything at once** - Work incrementally
5. **Don't forget tests** - Ensure tests still pass after refactoring
6. **Don't ignore documentation** - Update docs as you refactor

## Getting Help

If you're unsure about a refactoring:

1. Create an issue describing the refactoring
2. Tag it with `refactoring` label
3. Get feedback before starting
4. Reference this guide in your PR

## References

- [Architecture Decision Records](./ARCHITECTURE_DECISIONS.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Repository Layout Issues](https://github.com/your-org/jupyter/issues?q=is%3Aissue+label%3Alayout)



