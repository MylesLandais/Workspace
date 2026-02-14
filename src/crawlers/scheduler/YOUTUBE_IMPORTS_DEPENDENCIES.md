# Python Import Documentation and Dependency Graph

Complete documentation of all Python imports in the YouTube Feed system.

## Import Documentation by File

### 1. src/feed/services/youtube_enhanced_service.py

```python
# Standard Library
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4

# Project-specific
from feed.storage.neo4j_connection import get_connection
```

**Purpose:**
- `os`, `sys`: System operations and path manipulation
- `json`: JSON parsing for yt-dlp output
- `subprocess`: Running yt-dlp commands
- `Path`: File path handling
- `List, Dict, Optional, Any`: Type hints for collections
- `datetime`, `uuid4`: Timestamp and UUID generation
- `get_connection`: Neo4j database connection

### 2. media-platform/youtube_polling_worker.py

```python
# Standard Library
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Third-party
# None directly imported

# Project-specific
from feed.storage.neo4j_connection import get_connection
from feed.services.youtube_enhanced_service import YouTubeEnhancedService
```

**Purpose:**
- `time`: Sleep intervals for polling
- `logging`: Worker logging and monitoring
- `timedelta`: Date calculations for polling
- `YouTubeEnhancedService`: Enhanced YouTube data fetching

### 3. media-platform/youtube_enhanced_api.py

```python
# Third-party
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

# Project-specific
from feed.storage.neo4j_connection import get_connection
```

**Purpose:**
- `FastAPI`: REST API framework
- `HTTPException`, `Query`: API error handling and query parameters
- `BaseModel`: Pydantic data validation models
- `get_connection`: Neo4j database connection

### 4. init_youtube_schema.py

```python
# Standard Library
import sys
from pathlib import Path

# Project-specific
from feed.storage.neo4j_connection import get_connection
```

**Purpose:**
- `get_connection`: Neo4j database connection for schema initialization

### 5. test_youtube_enhanced.py

```python
# Standard Library
import sys
from pathlib import Path

# Project-specific
from feed.storage.neo4j_connection import get_connection
from feed.services.youtube_enhanced_service import YouTubeEnhancedService
```

**Purpose:**
- `get_connection`: Verification queries
- `YouTubeEnhancedService`: Test enhanced YouTube features

### 6. media-platform/services/youtube_analytics_service.py

```python
# Standard Library
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter

# Project-specific
from feed.storage.neo4j_connection import get_connection
```

**Purpose:**
- `Counter`: Count collections for keyword analysis
- `timedelta`: Time range calculations for trends
- `get_connection`: Neo4j database queries for analytics

### 7. media-platform/services/comment_thread_service.py

```python
# Standard Library
from typing import Dict, List, Optional
from collections import defaultdict

# Project-specific
from feed.storage.neo4j_connection import get_connection
```

**Purpose:**
- `defaultdict`: Dictionary with default values for thread building
- `get_connection`: Neo4j queries for comment threading

### 8. media-platform/youtube_analytics_api.py

```python
# Third-party
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Project-specific
from media_platform.services.youtube_analytics_service import YouTubeAnalytics
from media_platform.services.comment_thread_service import CommentThread
```

**Purpose:**
- `FastAPI`: API route registration
- `HTTPException`, `Query`: API error handling
- `BaseModel`: Pydantic models for responses
- `YouTubeAnalytics`: Analytics calculations
- `CommentThread`: Comment threading operations

### 9. src/feed/services/youtube_subscription_service.py (Existing)

```python
# Standard Library
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from uuid import UUID, uuid4
import json

# Third-party
from dotenv import load_dotenv

# Project-specific
from feed.storage.neo4j_connection import get_connection
from feed.storage.valkey_connection import get_valkey_connection
from feed.models.creator import Creator
from feed.models.handle import Handle
from feed.models.platform import Platform
from feed.ontology.schema import HandleStatus, VerificationConfidence
```

**Purpose:**
- `load_dotenv`: Environment variable loading
- `get_valkey_connection`: Redis caching connection
- `Creator`, `Handle`, `Platform`: Model classes
- `HandleStatus`, `VerificationConfidence`: Ontology enums

### 10. find_developer_creator.py (Created earlier)

```python
# Standard Library
import sys
from pathlib import Path
from uuid import uuid4

# Third-party
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Project-specific
from feed.storage.neo4j_connection import get_connection (used in earlier version)
```

**Purpose:**
- `GraphDatabase`: Direct Neo4j driver connection
- `load_dotenv`: Environment configuration

## Dependency Graph

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YouTube Feed System                        │
└─────────────────────────────────────────────────────────────────────┘

                            │
                            ▼
        ┌───────────────────────────────────┐
        │     Python Standard Library      │
        │  (os, sys, json, subprocess, │
        │   pathlib, datetime, uuid,     │
        │   typing, collections, logging) │
        └───────────────────────────────────┘
                    │
                    │ is used by
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Core Services Layer                         │
└─────────────────────────────────────────────────────────────────────┘
        │
        ├──────────────────┬──────────────────┬──────────────┐
        ▼                  ▼                  ▼              ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐ ┌──────────────┐
│     Neo4j    │   │   FastAPI    │   │   yt-dlp    │ │   Pydantic   │
│   Connection   │   │   Framework   │   │   Wrapper    │ │ Validation  │
│              │   │              │   │              │ │              │
│ - execute_   │   │ - FastAPI    │   │ - subprocess│   │ - BaseModel  │
│   read       │   │ - HTTPException│   │   - JSON     │   │ - Field      │
│ - execute_   │   │ - Query       │   │              │   │              │
│   write      │   │              │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘ └──────────────┘
        │                  │                  │              │
        │ imports          │ uses             │ uses          │ uses
        ▼                  ▼                  ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Service Layer                             │
└─────────────────────────────────────────────────────────────────────┘
        │
        ├──────────────────────────┬──────────────────┐
        ▼                      ▼                  ▼
┌──────────────────────┐  ┌──────────────────────┐ ┌──────────────────┐
│ YouTubeEnhanced    │  │ YouTubeAnalytics    │ │ CommentThread     │
│ Service            │  │ Service            │ │ Service           │
│                    │  │                    │ │                  │
│ - fetch_video_      │  │ - get_video_       │ │ - get_comment_   │
│   metadata         │  │   analytics         │ │   thread          │
│ - store_video_      │  │ - get_creator_     │ │ - store_comment_  │
│   with_all_        │  │   analytics         │ │   thread          │
│   features         │  │ - get_comment_     │ │ - get_comment_   │
│ - _fetch_comments   │  │   sentiment_        │ │   context         │
│ - _fetch_related   │  │   overview         │ │ - get_longest_   │
│   videos           │  │ - get_comment_     │ │   threads         │
│ - _store_chapters  │  │   engagement_       │ │                  │
│ - _store_comments  │  │   timeline         │ │                  │
│ - _store_transcript│  │ - get_top_         │ │                  │
│ - _extract_chapters│  │   commenters       │ │                  │
│ - _extract_        │  │ - get_video_       │ │                  │
│   transcript       │  │   trends           │ │                  │
│ - _format_         │  │ - get_keyword_     │ │                  │
│   timestamp        │  │   analysis         │ │                  │
│                    │  │ - get_channel_     │ │                  │
└──────────────────────┘  │  comparison         │ └──────────────────┘
                         │
                         └──────────────────┬──────────────────┐
                                          ▼                  ▼
                           ┌──────────────────────┐ ┌──────────────────┐
                           │ YouTubeEnhanced    │ │ Analytics API     │
                           │ API                │ │                  │
                           │                    │ │ - FastAPI        │
                           │ - FastAPI          │ │ - HTTPException   │
                           │ - HTTPException     │ │ - Query          │
                           │ - Query             │ │ - Pydantic       │
                           │ - Pydantic         │ │                  │
                           └──────────────────────┘ └──────────────────┘
                                          │
                                          │ serves
                                          ▼
                           ┌──────────────────────┐
                           │   YouTubePolling    │
                           │   Worker           │
                           │                    │
                           │ - logging          │
                           │ - time/sleep       │
                           │ - YouTubeEnhanced  │
                           │   Service         │
                           └──────────────────────┘

                            │
                            │ stores data in
                            ▼
                ┌──────────────────────────┐
                │      Neo4j Database   │
                │                        │
                │ - YouTubeVideo nodes  │
                │ - YouTubeComment nodes│
                │ - YouTubeChapter nodes│
                │ - YouTubeTranscript   │
                │   nodes             │
                │ - Relationships:      │
                │   HAS_COMMENT       │
                │   HAS_CHAPTER       │
                │   HAS_TRANSCRIPT_    │
                │   SEGMENT           │
                │   PARENT_OF         │
                │   PUBLISHED         │
                │   RELATED_TO        │
                └──────────────────────────┘
```

### Textual Dependency Graph

```
Standard Library
├── os
├── sys
├── json
├── subprocess
├── pathlib
├── datetime
├── uuid
├── typing
│   ├── List
│   ├── Dict
│   ├── Optional
│   └── Any
├── collections
│   ├── Counter
│   └── defaultdict
└── logging

Third-Party Dependencies
├── fastapi
│   ├── FastAPI
│   ├── HTTPException
│   └── Query
├── pydantic
│   ├── BaseModel
│   └── Field (implied)
├── neo4j
│   └── GraphDatabase
└── python-dotenv
    └── load_dotenv

Project-Specific Dependencies
├── feed.storage.neo4j_connection
│   └── get_connection
├── feed.storage.valkey_connection
│   └── get_valkey_connection
├── feed.models
│   ├── Creator
│   ├── Handle
│   └── Platform
├── feed.ontology.schema
│   ├── HandleStatus
│   └── VerificationConfidence
└── feed.services
    ├── youtube_enhanced_service
    │   └── YouTubeEnhancedService
    └── youtube_subscription_service
        └── YouTubeSubscriptionService
```

## Dependency Matrix

### By Layer

#### 1. Infrastructure Layer
```python
# Database Connections
from feed.storage.neo4j_connection import get_connection
from feed.storage.valkey_connection import get_valkey_connection

# Environment Configuration
from dotenv import load_dotenv
```

#### 2. Data Model Layer
```python
# Core Models
from feed.models.creator import Creator
from feed.models.handle import Handle
from feed.models.platform import Platform

# Ontology
from feed.ontology.schema import HandleStatus, VerificationConfidence
```

#### 3. Service Layer
```python
# YouTube Data Services
from feed.services.youtube_enhanced_service import YouTubeEnhancedService
from feed.services.youtube_subscription_service import YouTubeSubscriptionService

# Analytics Services
from media_platform.services.youtube_analytics_service import YouTubeAnalytics
from media_platform.services.comment_thread_service import CommentThread
```

#### 4. API Layer
```python
# REST API Framework
from fastapi import FastAPI, HTTPException, Query

# Data Validation
from pydantic import BaseModel
```

### By Module

#### Module: youtube_enhanced_service.py

**Imports:**
- Standard: os, sys, json, subprocess, Path, List, Dict, Optional, Any, datetime, uuid4
- Project: get_connection (Neo4j)

**Dependencies:**
- neo4j (via get_connection)
- yt-dlp (via subprocess)

**Dependents:**
- youtube_polling_worker.py
- youtube_enhanced_api.py
- test_youtube_enhanced.py

#### Module: youtube_polling_worker.py

**Imports:**
- Standard: os, sys, time, logging, Path, List, Dict, Optional, datetime, timedelta
- Project: get_connection, YouTubeEnhancedService

**Dependencies:**
- neo4j (via get_connection)
- YouTubeEnhancedService
- yt-dlp (via YouTubeEnhancedService)

**Dependents:**
- None (entry point for background jobs)

#### Module: youtube_enhanced_api.py

**Imports:**
- Standard: List, Optional, datetime, json
- Third-party: FastAPI, HTTPException, Query, BaseModel
- Project: get_connection

**Dependencies:**
- neo4j (via get_connection)
- fastapi
- pydantic

**Dependents:**
- None (serves HTTP requests)

#### Module: youtube_analytics_service.py

**Imports:**
- Standard: Dict, List, Optional, datetime, timedelta, Counter
- Project: get_connection

**Dependencies:**
- neo4j (via get_connection)

**Dependents:**
- youtube_analytics_api.py

#### Module: comment_thread_service.py

**Imports:**
- Standard: Dict, List, Optional, defaultdict
- Project: get_connection

**Dependencies:**
- neo4j (via get_connection)

**Dependents:**
- youtube_analytics_api.py

#### Module: youtube_analytics_api.py

**Imports:**
- Standard: List, Optional, datetime
- Third-party: FastAPI, HTTPException, Query, BaseModel
- Project: YouTubeAnalytics, CommentThread

**Dependencies:**
- fastapi
- pydantic
- YouTubeAnalytics
- CommentThread

**Dependents:**
- None (serves HTTP requests)

#### Module: youtube_subscription_service.py (Existing)

**Imports:**
- Standard: sys, Path, datetime, timedelta, UUID, uuid4, json
- Third-party: load_dotenv
- Project: get_connection, get_valkey_connection, Creator, Handle, Platform, HandleStatus, VerificationConfidence

**Dependencies:**
- neo4j (via get_connection)
- redis (via get_valkey_connection)
- python-dotenv

**Dependents:**
- Multiple (subscription management)

## Circular Dependencies

**None detected.** The dependency graph is acyclic:

```
API Layer → Service Layer → Storage Layer → Database
    ↓
External Services (yt-dlp)
```

## External Dependencies

### Required Packages

```txt
# Core
neo4j>=5.0.0
python-dotenv>=1.0.0

# API Framework
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0,<3.0.0

# YouTube Data Fetching
yt-dlp>=2023.1.0

# Caching (Optional)
redis>=4.5.0
```

### Installation

```bash
# Core dependencies
pip install neo4j python-dotenv

# API dependencies
pip install fastapi uvicorn pydantic

# YouTube dependencies
pip install yt-dlp

# All together
pip install -r requirements.txt
```

## Import Safety Analysis

### Safe Imports (No Side Effects)

✓ `from typing import List, Dict, Optional, Any`
✓ `from datetime import datetime, timedelta`
✓ `from uuid import uuid4`
✓ `from pathlib import Path`
✓ `from collections import Counter, defaultdict`
✓ `from fastapi import FastAPI, HTTPException, Query`
✓ `from pydantic import BaseModel`

### Imports with Potential Side Effects

⚠️ `from feed.storage.neo4j_connection import get_connection`
  - Side effect: Establishes database connection on first call
  - Safe: Singleton pattern manages connection lifecycle

⚠️ `from feed.storage.valkey_connection import get_valkey_connection`
  - Side effect: Establishes Redis connection on first call
  - Safe: Singleton pattern manages connection lifecycle

⚠️ `import subprocess`
  - Side effect: Spawns system processes
  - Safe: Explicit use in _run_ytdlp method

## Dependency Injection Opportunities

### Current Implementation

```python
# Hardcoded imports
from feed.storage.neo4j_connection import get_connection

class YouTubeEnhancedService:
    def __init__(self):
        self.neo4j = get_connection()  # Hard dependency
```

### Recommended Improvement

```python
# Dependency injection
from typing import Protocol

class DatabaseConnection(Protocol):
    def execute_read(self, query: str, parameters: dict) -> list: ...
    def execute_write(self, query: str, parameters: dict) -> list: ...

class YouTubeEnhancedService:
    def __init__(self, db: DatabaseConnection):
        self.neo4j = db  # Injected dependency

# Usage
from feed.storage.neo4j_connection import get_connection
service = YouTubeEnhancedService(db=get_connection())
```

## Module Responsibility Map

| Module | Responsibility | Key Imports |
|--------|--------------|--------------|
| `youtube_enhanced_service.py` | Fetch/store YouTube data with full features | Neo4j, subprocess, json |
| `youtube_polling_worker.py` | Monitor channels for new videos | YouTubeEnhancedService, logging, time |
| `youtube_enhanced_api.py` | REST API for video data | FastAPI, Pydantic, Neo4j |
| `youtube_analytics_service.py` | Calculate video/comment analytics | Neo4j, Counter, datetime |
| `comment_thread_service.py` | Manage comment hierarchies | Neo4j, defaultdict |
| `youtube_analytics_api.py` | REST API for analytics | FastAPI, YouTubeAnalytics, CommentThread |
| `youtube_subscription_service.py` | Manage channel subscriptions | Neo4j, Redis, Models |

## Summary

### Total Unique Imports by Category

**Standard Library:** 15 modules
- os, sys, json, subprocess, pathlib, datetime, uuid, typing, collections, logging, time, urllib

**Third-Party:** 4 packages
- fastapi, pydantic, neo4j, python-dotenv

**Project-Specific:** 8 modules
- feed.storage.neo4j_connection
- feed.storage.valkey_connection
- feed.models.creator
- feed.models.handle
- feed.models.platform
- feed.ontology.schema
- feed.services.youtube_enhanced_service
- feed.services.youtube_subscription_service

**External Tools:** 1
- yt-dlp (via subprocess)

### Dependency Complexity Score

**Low Complexity (Score: 3/10)**
- Minimal third-party dependencies
- Clear separation of concerns
- No circular dependencies
- Mostly standard library usage

### Maintenance Recommendations

1. **Add Type Hints:** Improve typing annotations across all modules
2. **Dependency Injection:** Consider DI for better testability
3. **Error Handling:** Standardize error handling patterns
4. **Logging:** Implement unified logging strategy
5. **Configuration:** Centralize configuration management
6. **Testing:** Add unit tests for each service module
