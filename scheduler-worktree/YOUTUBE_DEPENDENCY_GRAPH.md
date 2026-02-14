# YouTube Feed System - Dependency Graph

This document provides a visual and textual representation of the complete dependency graph for the YouTube Feed system.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                             │
│  (Browsers, CLI tools, API consumers)                                  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  │ HTTP/REST
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                            │
│  - youtube_enhanced_api.py                                           │
│  - youtube_analytics_api.py                                          │
└─────────────────────────┬───────────────────────────────────────────────┘
                        │
                        │ calls
                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Service Layer                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ YouTube      │  │ YouTube      │  │ Comment      │        │
│  │ Enhanced     │  │ Analytics     │  │ Thread       │        │
│  │ Service      │  │ Service      │  │ Service      │        │
│  │              │  │              │  │              │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          │ imports        │ imports        │ imports
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Storage Layer                                 │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │ Neo4j        │  │ Redis        │                              │
│  │ Connection    │  │ Connection   │                              │
│  │              │  │              │                              │
│  └──────┬───────┘  └──────┬───────┘                              │
└─────────┼─────────────────┼──────────────────────────────────────────────┘
          │                 │
          │ queries          │ caches
          ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Data Layer                                    │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │ Neo4j DB     │  │ Redis Cache  │                              │
│  │              │  │              │                              │
│  │ Nodes:       │  │ Keys:        │                              │
│  │ - Video      │  │ - creator:*  │                              │
│  │ - Comment    │  │ - video:*    │                              │
│  │ - Chapter    │  │ - search:*  │                              │
│  │ - Transcript │  │              │                              │
│  │              │  │              │                              │
│  └──────────────┘  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          │ system calls
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   External Services                               │
│  ┌──────────────┐                                               │
│  │ yt-dlp       │                                               │
│  │              │                                               │
│  │ Fetches:     │                                               │
│  │ - Video      │                                               │
│  │ - Comments   │                                               │
│  │ - Captions   │                                               │
│  │ - Metadata   │                                               │
│  │              │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Module Dependencies

### 1. YouTube Enhanced Service

```
youtube_enhanced_service.py
│
├─> Standard Library
│   ├─ os (environment variables)
│   ├─ sys (path manipulation)
│   ├─ json (parse yt-dlp output)
│   ├─ subprocess (run yt-dlp)
│   ├─ Path (file operations)
│   ├─ datetime (timestamps)
│   ├─ uuid (generate unique IDs)
│   └─ typing (type hints)
│
├─> Storage Layer
│   └─ feed.storage.neo4j_connection
│       └─> Neo4j driver
│           └─> neo4j package
│
└─> External Services
    └─ subprocess
        └─> yt-dlp (YouTube API wrapper)
```

**Dependency Level:** 2 (Standard → Storage → External)

### 2. YouTube Enhanced API

```
youtube_enhanced_api.py
│
├─> Standard Library
│   ├─ List, Optional (type hints)
│   ├─ datetime (timestamps)
│   └─ json (parse tags/categories)
│
├─> Third-Party
│   ├─ fastapi (web framework)
│   │   ├─ FastAPI
│   │   ├─ HTTPException
│   │   └─ Query (parameter parsing)
│   └─ pydantic (data validation)
│       └─ BaseModel
│
└─> Storage Layer
    └─ feed.storage.neo4j_connection
        └─> Neo4j driver
```

**Dependency Level:** 2 (Standard → Third-Party → Storage)

### 3. YouTube Analytics Service

```
youtube_analytics_service.py
│
├─> Standard Library
│   ├─ Dict, List, Optional (type hints)
│   ├─ datetime (time calculations)
│   ├─ timedelta (date ranges)
│   └─ collections
│       └─ Counter (keyword analysis)
│
└─> Storage Layer
    └─ feed.storage.neo4j_connection
        └─> Neo4j driver
```

**Dependency Level:** 2 (Standard → Storage)

### 4. Comment Thread Service

```
comment_thread_service.py
│
├─> Standard Library
│   ├─ Dict, List, Optional (type hints)
│   └─ collections
│       └─ defaultdict (thread hierarchy)
│
└─> Storage Layer
    └─ feed.storage.neo4j_connection
        └─> Neo4j driver
```

**Dependency Level:** 2 (Standard → Storage)

### 5. YouTube Polling Worker

```
youtube_polling_worker.py
│
├─> Standard Library
│   ├─ os (environment)
│   ├─ sys (path)
│   ├─ time (sleep intervals)
│   ├─ logging (worker logs)
│   ├─ Path (file operations)
│   ├─ datetime (timestamps)
│   ├─ timedelta (poll intervals)
│   └─ typing (type hints)
│
└─> Service Layer
    ├─ feed.storage.neo4j_connection
    │   └─> Neo4j driver
    │
    └─ feed.services.youtube_enhanced_service
        │   ├─> Standard Library
        │   ├─> Storage Layer (Neo4j)
        │   └─> External (yt-dlp)
```

**Dependency Level:** 3 (Standard → Service → Storage → External)

### 6. YouTube Analytics API

```
youtube_analytics_api.py
│
├─> Standard Library
│   ├─ List, Optional (type hints)
│   └─ datetime (timestamps)
│
├─> Third-Party
│   ├─ fastapi
│   │   ├─ FastAPI
│   │   ├─ HTTPException
│   │   └─ Query
│   └─ pydantic
│       └─ BaseModel
│
└─> Service Layer
    ├─ media_platform.services.youtube_analytics_service
    │   └─> Standard + Storage
    │
    └─ media_platform.services.comment_thread_service
        └─> Standard + Storage
```

**Dependency Level:** 3 (Standard → Third-Party → Service)

### 7. YouTube Subscription Service (Existing)

```
youtube_subscription_service.py
│
├─> Standard Library
│   ├─ sys, Path (path manipulation)
│   ├─ datetime, timedelta (timestamps)
│   ├─ UUID, uuid4 (unique IDs)
│   ├─ json (serialize data)
│   └─ typing (type hints)
│
├─> Third-Party
│   └─ python-dotenv
│       └─ load_dotenv
│
├─> Storage Layer
│   ├─ feed.storage.neo4j_connection
│   │   └─> Neo4j driver
│   │
│   └─ feed.storage.valkey_connection
│       └─> Redis driver
│
└─> Model Layer
    ├─ feed.models.creator
    ├─ feed.models.handle
    ├─ feed.models.platform
    └─ feed.ontology.schema
        ├─ HandleStatus
        └─ VerificationConfidence
```

**Dependency Level:** 4 (Standard → Third-Party → Storage → Models)

## Dependency Flow Diagrams

### Data Ingestion Flow

```
YouTube Polling Worker
    │
    ├─> YouTubeEnhancedService.fetch_video_metadata()
    │       │
    │       ├─> subprocess (yt-dlp)
    │       │       └─> YouTube API
    │       │
    │       └─> Neo4j.execute_write()
    │               └─> Neo4j Database
    │
    └─> Neo4j.execute_write() (update poll status)
            └─> Neo4j Database
```

### API Request Flow

```
Client Request
    │
    ▼
FastAPI Route Handler (youtube_enhanced_api.py)
    │
    ├─> Validate with Pydantic
    │
    └─> Neo4j.execute_read()
            │
            └─> Neo4j Database
                    │
                    ├─> YouTubeVideo node
                    ├─> YouTubeComment nodes
                    ├─> YouTubeChapter nodes
                    └─> YouTubeTranscript nodes
                    │
                    ▼
            Return JSON Response to Client
```

### Analytics Calculation Flow

```
Client Request Analytics
    │
    ▼
FastAPI Route Handler (youtube_analytics_api.py)
    │
    ├─> YouTubeAnalytics.calculate()
    │       │
    │       └─> Neo4j.execute_read()
    │               └─> Neo4j Database
    │
    └─> Return JSON Response
```

### Comment Threading Flow

```
Request Comment Thread
    │
    ▼
FastAPI Route Handler (youtube_analytics_api.py)
    │
    ├─> CommentThread.get_comment_thread()
    │       │
    │       └─> Neo4j.execute_read()
    │               └─> Neo4j Database
    │                       │
    │                       ├─> Comments
    │                       ├─> PARENT_OF relationships
    │                       └─> HAS_COMMENT relationships
    │
    └─> Build Tree (defaultdict)
            └─> Return Hierarchy
```

## Import Summary by Category

### Database Connections (3 modules)
```python
from feed.storage.neo4j_connection import get_connection  # 6 modules
from feed.storage.valkey_connection import get_valkey_connection  # 1 module
import neo4j  # 1 module (direct driver)
```

### YouTube Services (2 modules)
```python
from feed.services.youtube_enhanced_service import YouTubeEnhancedService  # 2 modules
from feed.services.youtube_subscription_service import YouTubeSubscriptionService  # 1 module
```

### Media Services (2 modules)
```python
from media_platform.services.youtube_analytics_service import YouTubeAnalytics  # 1 module
from media_platform.services.comment_thread_service import CommentThread  # 1 module
```

### Data Models (4 modules)
```python
from feed.models.creator import Creator  # 1 module
from feed.models.handle import Handle  # 1 module
from feed.models.platform import Platform  # 1 module
from feed.ontology.schema import HandleStatus, VerificationConfidence  # 1 module
```

### API Framework (2 modules)
```python
from fastapi import FastAPI, HTTPException, Query  # 2 modules
from pydantic import BaseModel  # 2 modules
```

### External Tools (1 module)
```python
import subprocess  # 2 modules
    └─> yt-dlp
```

## Dependency Risk Analysis

### Low Risk (No External Runtime Dependencies)

✓ Standard Library: 15 modules
✓ Neo4j Driver: Stable, well-tested
✓ FastAPI: Production-ready, stable
✓ Pydantic: Production-ready, stable
✓ yt-dlp: Regularly updated, MIT licensed

### Medium Risk (Requires External Service)

⚠️ yt-dlp: Depends on YouTube API
  - Risk: API rate limits, policy changes
  - Mitigation: Implement caching, exponential backoff

### No Circular Dependencies

✓ All dependencies flow in one direction
✓ No module A imports module B, B imports module A
✓ Clear layer separation (API → Service → Storage)

## Performance Considerations

### Database Connection Pooling

```
get_connection()
    │
    ├─ Singleton pattern
    ├─ Connection pooling (Neo4j driver)
    └─ Automatic connection reuse

Benefits:
✓ Reduced connection overhead
✓ Better resource utilization
✓ Improved query performance
```

### Caching Strategy

```
Redis (via valkey_connection)
    │
    ├─ Cache keys: "creator:*", "video:*"
    ├─ TTL: 3600 seconds (1 hour)
    └─ Invalidation: On data updates

Benefits:
✓ Reduced database load
✓ Faster response times
✓ Better scalability
```

### Batch Processing

```
YouTubeEnhancedService
    │
    ├─> Fetch videos in batches (channel polling)
    ├─> Store comments in batches (UNWIND)
    └─> Store transcripts in batches (UNWIND)

Benefits:
✓ Reduced network round trips
✓ Better transaction efficiency
✓ Improved throughput
```

## Scaling Recommendations

### Horizontal Scaling

```
Multiple API Instances
    │
    ├─> Load Balancer
    │       │
    │       ├─> API Instance 1
    │       ├─> API Instance 2
    │       └─> API Instance N
    │
    └─> Shared Neo4j Cluster
            │
            ├─> Primary Node
            ├─> Replica Node 1
            └─> Replica Node N
```

### Vertical Scaling

```
Single Instance Optimization
    │
    ├─> Connection Pool Size (adjust for workload)
    ├─> Query Optimization (use indexes)
    ├─> Caching (Redis)
    └─> Batch Processing (reduce round trips)
```

## Monitoring Points

### Key Metrics to Monitor

1. **API Layer**
   - Request rate (RPS)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)

2. **Service Layer**
   - YouTube fetch success rate
   - yt-dlp command duration
   - Storage write latency

3. **Storage Layer**
   - Neo4j query duration
   - Connection pool usage
   - Cache hit/miss ratio

4. **External Services**
   - YouTube API rate limit usage
   - yt-dlp version compatibility
   - Network latency to YouTube

## Maintenance Considerations

### Update Strategy

```
Weekly:
├─ Update yt-dlp (bug fixes, features)
└─ Check Neo4j driver updates

Monthly:
├─ Update FastAPI/Pydantic (security patches)
└─ Review Neo4j schema for optimizations

Quarterly:
├─ Update Python version (if major)
└─ Re-evaluate external dependencies
```

### Rollback Plan

```
If Issues Detected:
├─ 1. Revert last dependency update
├─ 2. Check Neo4j data integrity
├─ 3. Verify API functionality
└─ 4. Monitor error logs
```

## Dependency Version Matrix

| Dependency | Minimum Version | Recommended Version | Last Updated |
|------------|-----------------|---------------------|---------------|
| neo4j | 5.0.0 | 5.26.0 | 2025-01 |
| fastapi | 0.100.0 | 0.115.0 | 2024-12 |
| pydantic | 2.0.0 | 2.10.0 | 2024-12 |
| python-dotenv | 1.0.0 | 1.1.1 | 2024-12 |
| yt-dlp | 2023.1.0 | 2025.1.0 | 2025-01 |

## Summary

### System Characteristics

- **Total Modules:** 8 Python modules
- **Total Dependencies:** 8 external packages
- **Dependency Depth:** Max 4 layers
- **Circular Dependencies:** 0
- **External Service Dependencies:** 1 (yt-dlp)
- **Database Dependencies:** 2 (Neo4j, Redis)

### Architectural Quality

✓ **Separation of Concerns:** Clear layer boundaries
✓ **Loose Coupling:** Minimal inter-module dependencies
✓ **High Cohesion:** Each module has single responsibility
✓ **Testability:** Can test modules in isolation
✓ **Scalability:** Supports horizontal scaling
✓ **Maintainability:** Easy to add/remove features

### Risk Assessment

- **Overall Risk Level:** Low
- **External Dependencies:** Minimal
- **Legacy Code:** None
- **Known Issues:** None
- **Security:** No critical vulnerabilities

### Recommendations

1. Implement comprehensive error handling
2. Add integration tests for all services
3. Set up monitoring and alerting
4. Document API versioning strategy
5. Plan for dependency updates
