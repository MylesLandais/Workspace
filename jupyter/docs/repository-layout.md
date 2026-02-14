# Repository Layout Guide

This document explains the target repository structure and provides guidance on where to place new code.

## Current Problems

The repository has suffered from several layout issues:

1. **Top-level script proliferation**: Many utility scripts (`check_*.py`, `crawl_*.py`, `download_*.py`) clutter the root directory
2. **Inconsistent module organization**: Related functionality scattered across different directories
3. **Mixed concerns**: Scripts, libraries, notebooks, and documentation intermingled
4. **Unclear boundaries**: Unclear separation between production code, utilities, and experiments

## Target Structure

```
jupyter/
├── src/                          # Production code (installable packages)
│   ├── feed/                     # Feed/crawler system
│   │   ├── platforms/            # Platform adapters (Reddit, Depop, etc.)
│   │   ├── crawler/              # Crawler engine
│   │   ├── storage/              # Storage abstractions (Neo4j, MinIO, etc.)
│   │   ├── services/             # Business logic services
│   │   └── models/               # Data models
│   ├── image_dedup/              # Image deduplication system
│   ├── image_captioning/          # Image captioning system
│   ├── image_crawler/            # Image crawling system
│   ├── providers/                # External service providers
│   │   ├── asr/                  # ASR model providers
│   │   └── vlm/                  # Vision-language model providers
│   ├── datasets/                 # Dataset management
│   ├── infra/                    # Infrastructure utilities
│   └── config/                   # Configuration management
│
├── scripts/                      # Utility scripts (not installable)
│   ├── monitoring/               # Status checks, health monitoring
│   │   ├── check_neo4j_status.py
│   │   ├── check_runpod_pod_logs.py
│   │   └── monitor_crawlers.sh
│   ├── crawling/                 # Crawler utilities
│   │   ├── crawl_reddit_subreddit.py
│   │   └── fast_thread_crawler.py
│   ├── data_processing/          # Data transformation scripts
│   │   ├── download_all_thread_images.py
│   │   └── organize_imageboard_images.py
│   ├── deployment/               # Deployment automation
│   └── archive/                  # Deprecated/archived scripts
│
├── notebooks/                    # Jupyter notebooks
│   ├── examples/                 # Example workflows
│   ├── experiments/              # Experimental work
│   └── runpod_deployments/       # RunPod deployment notebooks
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
│
├── docs/                         # Documentation
│   ├── architecture/             # Architecture decisions
│   ├── guides/                   # User guides
│   └── api/                      # API documentation
│
├── agents/                       # Agent implementations
│   └── [agent-name]/            # Individual agent projects
│
├── media-platform/               # Media platform application
│   └── [Node.js application structure]
│
├── config/                       # Configuration files
│   └── [config files]
│
├── data/                         # Data files (git-ignored or LFS)
│   └── [data files]
│
├── docker/                       # Docker-related files
│   └── [Dockerfiles, docker-compose files]
│
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project configuration
├── docker-compose.yml            # Docker Compose configuration
├── README.md                     # Main README
├── CONTRIBUTING.md               # Contributing guidelines
└── .env.example                  # Environment variable template
```

## Directory Purposes

### `src/` - Production Code

**Purpose**: Installable Python packages that provide reusable functionality.

**Rules**:
- Code here should be importable: `from src.feed.platforms.reddit import RedditAdapter`
- Each module should have a clear, single responsibility
- Modules should be well-tested
- Include `__init__.py` files to make packages importable
- Include README.md in each major module

**Examples**:
- `src/feed/platforms/reddit.py` - Reddit platform adapter
- `src/feed/storage/neo4j_connection.py` - Neo4j connection management
- `src/image_dedup/deduplicator.py` - Image deduplication logic

### `scripts/` - Utility Scripts

**Purpose**: Standalone scripts that use code from `src/` but are not themselves importable.

**Rules**:
- Scripts should be executable from command line
- Scripts should import from `src/`, not from each other
- Organize by function (monitoring, crawling, data_processing, etc.)
- Include shebang and docstring explaining purpose
- Can be shell scripts (`.sh`) or Python scripts (`.py`)

**Examples**:
- `scripts/monitoring/check_neo4j_status.py` - Health check script
- `scripts/crawling/crawl_reddit_subreddit.py` - Crawler entry point
- `scripts/data_processing/organize_imageboard_images.py` - Data organization script

### `notebooks/` - Jupyter Notebooks

**Purpose**: Interactive exploration, examples, and experiments.

**Rules**:
- `notebooks/examples/` - Well-documented example workflows
- `notebooks/experiments/` - Experimental work, can be messy
- `notebooks/runpod_deployments/` - Deployment automation notebooks
- Notebooks should be git-tracked (not in .gitignore)
- Include markdown cells explaining purpose

**Examples**:
- `notebooks/examples/depop_crawler_example.ipynb` - Example of using Depop adapter
- `notebooks/experiments/taylor_swift_reddit_tracker.ipynb` - Experimental tracking
- `notebooks/runpod_deployments/deploy_comfy_3090.ipynb` - Deployment automation

### `tests/` - Test Suite

**Purpose**: All tests for the codebase.

**Rules**:
- Mirror `src/` structure: `tests/unit/src/feed/platforms/test_reddit.py`
- Use descriptive test names
- Follow pytest conventions
- Include fixtures and test utilities

**Examples**:
- `tests/unit/src/feed/platforms/test_reddit.py` - Unit tests for Reddit adapter
- `tests/integration/test_feed_system.py` - Integration tests
- `tests/e2e/test_crawler_workflow.py` - End-to-end tests

### `docs/` - Documentation

**Purpose**: All project documentation.

**Rules**:
- Use Markdown format
- Organize by topic (architecture, guides, api)
- Keep documentation up-to-date with code
- Include diagrams when helpful

**Examples**:
- `docs/ARCHITECTURE_DECISIONS.md` - Architecture Decision Records
- `docs/WRITING_USER_STORIES.md` - Guide for writing stories
- `docs/REFACTORING_GUIDELINES.md` - Refactoring best practices

### `agents/` - Agent Implementations

**Purpose**: Self-contained agent projects.

**Rules**:
- Each agent is a separate project
- Follow agent template structure
- Include README.md explaining the agent
- Can have own dependencies and tests

**Examples**:
- `agents/rpg-graph-vtt/` - RPG Graph VTT agent
- `agents/comfy/` - ComfyUI agent

## Where to Put New Code

### Adding a New Feature

1. **Production code** → `src/[module]/`
   - Create new module if needed
   - Follow existing module structure
   - Add tests in `tests/unit/src/[module]/`

2. **CLI/script** → `scripts/[category]/`
   - Choose appropriate category (monitoring, crawling, etc.)
   - Create category directory if needed
   - Import from `src/`

3. **Example/experiment** → `notebooks/[examples|experiments]/`
   - Use `examples/` for well-documented examples
   - Use `experiments/` for exploratory work

4. **Documentation** → `docs/`
   - Add to appropriate section
   - Update README if needed

### Adding a New Platform Adapter

```
src/feed/platforms/
├── __init__.py
├── base.py              # Base adapter interface
├── reddit.py            # Existing
├── depop.py             # Existing
└── new_platform.py      # New adapter
```

### Adding a New Monitoring Script

```
scripts/monitoring/
├── check_neo4j_status.py    # Existing
└── check_new_service.py     # New script
```

### Adding a New Test

```
tests/unit/src/feed/platforms/
├── test_reddit.py           # Existing
└── test_new_platform.py     # New test
```

## Migration Guide

### Moving a Top-Level Script

1. Identify the script's purpose
2. Determine target directory (`scripts/[category]/`)
3. Move with git: `git mv script.py scripts/category/`
4. Update imports in the script
5. Update any references to the script
6. Test the script in its new location

### Consolidating Related Code

1. Identify all related files
2. Create target module in `src/`
3. Move files incrementally
4. Refactor to shared interfaces
5. Update all imports
6. Remove old files

See [REFACTORING_GUIDELINES.md](./REFACTORING_GUIDELINES.md) for detailed migration strategies.

## Naming Conventions

### Files and Directories

- **Modules**: `snake_case` (e.g., `image_dedup`, `feed_crawler`)
- **Scripts**: `snake_case` with verb prefix (e.g., `check_status.py`, `crawl_reddit.py`)
- **Directories**: `snake_case` (e.g., `data_processing`, `runpod_deployments`)

### Code

- **Classes**: `PascalCase` (e.g., `ProductStorage`, `DepopAdapter`)
- **Functions**: `snake_case` (e.g., `get_connection`, `store_product`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)

## Anti-Patterns to Avoid

1. **Don't create files in root** - Use appropriate subdirectory
2. **Don't mix concerns** - Keep scripts, libraries, and tests separate
3. **Don't create deep nesting** - Keep directory depth reasonable (max 4-5 levels)
4. **Don't duplicate code** - Extract to `src/` and import
5. **Don't ignore structure** - Follow the target structure even for small changes

## Getting Help

If you're unsure where to put something:

1. Check this guide
2. Look at similar existing code
3. Ask in an issue or PR
4. Reference this guide in your question

## References

- [Refactoring Guidelines](./REFACTORING_GUIDELINES.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Architecture Decisions](./ARCHITECTURE_DECISIONS.md)



