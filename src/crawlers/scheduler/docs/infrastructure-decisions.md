# Infrastructure Decisions and Architecture

**Last Updated:** January 2025  
**Status:** Active Documentation

This document records infrastructure decisions, architecture patterns, and deployment strategies for the development and production environments.

## Table of Contents

1. [Storage Provider Decisions](#storage-provider-decisions)
2. [Development Environment Architecture](#development-environment-architecture)
3. [Environment-Based Configuration](#environment-based-configuration)
4. [Test Data Management](#test-data-management)
5. [Production Deployment Strategy](#production-deployment-strategy)

---

## Storage Provider Decisions

### Decision: S3-Compatible Object Storage

**Selected Providers (in order of preference):**
1. **Cloudflare R2** (Primary choice)
2. **Google Cloud Storage** (Secondary)
3. **Oracle Cloud Object Storage** (Tertiary)

**Excluded Providers:**
- Azure (avoided per team preference)
- AWS (avoided per team preference)

### Cost Analysis for 1TB Monthly Storage

| Provider | Standard Storage | Infrequent Access | Free Egress | Notes |
|----------|-----------------|-------------------|-------------|-------|
| **Cloudflare R2** | $15.36/month | $10.24/month | Yes (unlimited) | Best value with free egress |
| **Google Cloud Storage** | $20.48/month | $10.24/month | 100GB/month | Good S3 compatibility |
| **Oracle Cloud** | $26.11/month | $10.24/month | 10TB/month | Highest standard pricing |

**Decision Rationale:**
- Cloudflare R2 offers the best cost-to-feature ratio with free egress bandwidth
- Free egress is critical for serving media to RunPod workers and other services
- All three providers offer S3-compatible APIs, enabling code portability
- Infrequent access tiers available for archival data at $10.24/month

### Additional Storage Costs

**Request and Operation Fees:**
- Cloudflare R2: $4.50 per million Class A operations (writes), $0.36 per million Class B operations (reads)
- Google Cloud: Minimal for standard workloads
- Oracle Cloud: Standard S3 operation pricing

**Egress Bandwidth:**
- Cloudflare R2: **Free** (unlimited)
- Google Cloud: $0.12/GB after 100GB free tier
- Oracle Cloud: $0.0085/GB after 10TB free tier

---

## Development Environment Architecture

### Stack Components

Our local development environment uses Docker Compose to orchestrate:

1. **MinIO** - S3-compatible object storage for local development
2. **Neo4j** - Graph database for storing media pointers and relationships
3. **Valkey** - Redis-compatible cache layer for query results and metadata
4. **PostgreSQL + pgvector** - Vector database for embeddings and search

### Docker Compose Services

See `docker-compose.yml` for the complete configuration. Key services:

#### MinIO (Object Storage)
- **Image:** `minio/minio:latest`
- **Ports:** 9000 (API), 9001 (Console)
- **Purpose:** Local S3-compatible storage mirroring production
- **Configuration:** Environment variables for credentials

#### Neo4j (Graph Database)
- **Image:** `neo4j:latest`
- **Ports:** 7474 (HTTP), 7687 (Bolt)
- **Purpose:** Store pointers to bucket objects (media like images/videos)
- **Configuration:** Separate instances per environment (dev/staging/prod)

#### Valkey (Cache Layer)
- **Image:** `valkey/valkey:7.2`
- **Port:** 6379
- **Purpose:** Cache Neo4j query results, object storage metadata, media URL resolution
- **Configuration:** LRU eviction policy, configurable memory limits

### Local Development Setup

**Prerequisites:**
- Docker and Docker Compose
- NixOS (for Nix-based deployments)

**Quick Start:**
```bash
# Start all services
docker compose up -d

# Access MinIO console
open http://localhost:9001

# Access Neo4j browser
open http://localhost:7474

# Access Valkey CLI
docker compose exec valkey valkey-cli
```

**Service Health Checks:**
All services include health checks and will restart automatically on failure.

---

## Environment-Based Configuration

### Configuration Strategy

We use environment variables to switch between local development (MinIO), staging, and production (GCP/Cloudflare R2) without code changes.

### S3-Compatible Storage Configuration

**Environment Variables:**
```bash
# Local Development (MinIO)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=dev-bucket
S3_REGION=us-east-1
S3_FORCE_PATH_STYLE=true

# Staging (Cloudflare R2)
S3_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<R2_ACCESS_KEY>
S3_SECRET_ACCESS_KEY=<R2_SECRET_KEY>
S3_BUCKET_NAME=staging-bucket
S3_REGION=auto
S3_FORCE_PATH_STYLE=true

# Production (Google Cloud Storage)
S3_ENDPOINT=https://storage.googleapis.com
S3_ACCESS_KEY_ID=<GCS_ACCESS_KEY>
S3_SECRET_ACCESS_KEY=<GCS_SECRET_KEY>
S3_BUCKET_NAME=production-bucket
S3_REGION=us-central1
S3_FORCE_PATH_STYLE=false
```

**SDK Configuration Pattern:**
All S3-compatible SDKs (boto3, AWS SDK, etc.) support these environment variables. The application code reads from environment variables, allowing seamless switching between environments.

### Neo4j Configuration

**Environment Variables:**
```bash
# Local Development
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=localpassword
NEO4J_DATABASE=neo4j

# Staging/Production
NEO4J_URI=neo4j+s://staging.example.com:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secure-password>
NEO4J_DATABASE=neo4j
```

**Multi-Environment Strategy:**
- **Development:** Local Neo4j → Local MinIO
- **Staging:** Staging Neo4j → GCP/Cloudflare staging bucket
- **Production:** Production Neo4j → GCP/Cloudflare production bucket

### Valkey Configuration

**Environment Variables:**
```bash
# Local Development
VALKEY_URL=valkey://localhost:6379
VALKEY_PASSWORD=
VALKEY_DB=0
VALKEY_TTL=300

# Staging/Production
VALKEY_URL=valkey://staging.example.com:6379
VALKEY_PASSWORD=<secure-password>
VALKEY_DB=0
VALKEY_TTL=300
```

### Storage Pointer Pattern

Neo4j nodes store object keys (not full URLs) to maintain portability:

```cypher
// Node structure with media pointers
CREATE (m:Media {
  id: 'unique-id',
  bucket: 'my-bucket',
  objectKey: 'path/to/video.mp4',
  thumbnailKey: 'path/to/thumbnail.jpg',
  createdAt: datetime()
})
```

Application code constructs full URLs using environment-specific endpoints:

```python
storage_base_url = os.getenv("S3_ENDPOINT", "https://storage.googleapis.com")
bucket_name = os.getenv("S3_BUCKET_NAME", "default-bucket")
full_url = f"{storage_base_url}/{bucket_name}/{node.objectKey}"
```

This approach keeps Neo4j data portable across environments while allowing flexible storage backends.

---

## Test Data Management

### Strategy: Self-Service Test Data Provisioning

We implement a distributed self-service model where developers can provision test environments in minutes using pre-built datasets.

### Dataset Structure

Test datasets are organized into discrete, named datasets:

- **Minimal:** Small graph with ~100 nodes, basic media objects for fast iteration
- **Standard:** Representative production-like dataset with ~10K nodes
- **Full:** Large-scale dataset for performance testing with ~1M nodes
- **Edge Cases:** Specialized datasets for testing error conditions and boundary scenarios

### Test Data Repository

```
test-data/
├── neo4j-dumps/
│   ├── minimal.dump
│   ├── standard.dump
│   └── full.dump
├── media-fixtures/
│   ├── images/
│   ├── videos/
│   └── manifest.json
└── scripts/
    ├── load-dataset.sh
    └── seed-storage.sh
```

### Neo4j Snapshot Workflow

**Creating Snapshots:**
```bash
# Create a dataset snapshot (run by data team)
neo4j-admin database dump neo4j --to-path=/snapshots/
```

**Restoring Snapshots:**
```bash
# Developers restore locally
neo4j-admin database load neo4j --from-path=/snapshots/ --overwrite-destination=true
```

### Coordinated Media Fixtures

Media fixtures are synchronized with Neo4j snapshots to ensure referential integrity:

```bash
#!/bin/bash
DATASET=$1  # minimal, standard, or full

# Load Neo4j dump
neo4j-admin database load neo4j --from-path=./test-data/neo4j-dumps/${DATASET}.dump

# Sync media fixtures to MinIO
mc mirror ./test-data/media-fixtures/${DATASET}/ local/test-bucket/

echo "Environment provisioned with ${DATASET} dataset"
```

### Valkey Cache Snapshots

For representative performance testing, Valkey cache states can be snapshotted:

```bash
# Save Valkey snapshot for test fixture
valkey-cli BGSAVE
cp /data/dump.rdb ./test-data/valkey-snapshots/standard.rdb
```

Developers can restore these snapshots to get pre-warmed caches matching their test datasets.

### Dedicated Development Databases

Each developer gets isolated environments to prevent conflicts:

```yaml
services:
  neo4j-dev:
    container_name: neo4j-${DEVELOPER_NAME}
  
  minio-dev:
    container_name: minio-${DEVELOPER_NAME}
```

### Data Subset Provisioning

For large datasets, developers can provision subsets based on business entities:

```cypher
// Extract a subset for specific test scenarios
MATCH path = (u:User {id: 'test-user-1'})-[*..3]-(connected)
WITH collect(nodes(path)) as nodeLists
UNWIND nodeLists as nodes
UNWIND nodes as n
RETURN DISTINCT n
```

---

## Production Deployment Strategy

### Staging and Production Migration

**Data Migration Workflow:**
1. Upload media to S3-compatible storage (MinIO/GCP/R2)
2. Create Neo4j node with object key only after successful upload
3. Store metadata (size, content-type, etag) in Neo4j for validation

**Synchronization Between Environments:**
Use MinIO Client (`mc`) to synchronize buckets:

```bash
# Set up aliases
mc alias set local http://localhost:9000 minioadmin minioadmin
mc alias set prod https://storage.googleapis.com GCS_ACCESS_KEY GCS_SECRET

# Mirror/sync data
mc mirror local/bucket-name prod/bucket-name
```

**URL Rewriting During Migration:**
When promoting data between environments, rewrite storage URLs in batch:

```cypher
// Update all media URLs to new environment
MATCH (m:Media)
WHERE m.storageUrl CONTAINS 'staging-bucket'
SET m.storageUrl = replace(m.storageUrl, 'staging-bucket', 'production-bucket')
RETURN count(m) as updatedNodes
```

### Consistency Considerations

**Transaction Coordination:**
Since Neo4j and object storage are separate systems, we implement a two-phase approach:
1. Upload media to storage first
2. Create Neo4j node only after successful upload
3. Store metadata in Neo4j for validation

**Validation Queries:**
Implement health checks to verify storage pointer integrity:

```cypher
// Find nodes with potentially missing media
MATCH (m:Media)
WHERE NOT exists(m.objectKey) OR m.objectKey = ''
RETURN m.id, m.createdAt
```

Run these checks after environment migrations to ensure data consistency.

### Caching Strategy

**Valkey Use Cases:**
- **Neo4j query results:** Store expensive graph traversal results with TTL expiration
- **Object storage metadata:** Cache S3 object metadata (size, content-type, etag) to avoid repeated HEAD requests
- **Media URL resolution:** Cache the mapping of Neo4j object keys to full storage URLs
- **Session data:** Store user sessions for high-traffic scenarios

**Cache-Aside Pattern:**
1. Check Valkey for cached data first
2. On cache miss, query Neo4j or storage backend
3. Store result in Valkey with TTL
4. Subsequent requests return data in microseconds

**Example Implementation:**
```python
async def get_media_node(media_id):
    cache_key = f"media:{media_id}"
    
    # Check cache first
    cached = await valkey_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Cache miss - query Neo4j
    result = await neo4j_session.run(
        'MATCH (m:Media {id: $id}) RETURN m',
        {'id': media_id}
    )
    
    # Store in Valkey with 5-minute TTL
    await valkey_client.setex(cache_key, 300, json.dumps(result))
    return result
```

---

## S3 API Compatibility Notes

### Cloudflare R2
- Full S3 API compatibility
- Endpoint format: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
- Use same S3 API calls and tools seamlessly

### Google Cloud Storage
- S3 compatibility with some limitations
- Incomplete implementations: `ListObjectVersions`, multipart uploads, multi-object delete
- Consider using GCS native APIs or ensure application doesn't rely on these specific S3 features

### MinIO
- Full S3 API compatibility
- Designed to run natively on Kubernetes across all cloud platforms
- Ideal for local development that accurately mirrors production behavior

---

## NixOS Deployment

For NixOS environments, services can be deployed using the NixOS module system:

**MinIO:**
```nix
services.minio = {
  enable = true;
  rootCredentialsFile = "/var/lib/minio/credentials";
  dataDir = "/var/lib/minio/data";
};
```

**Neo4j:**
```nix
services.neo4j = {
  enable = true;
  directories.home = "/var/lib/neo4j";
};
```

The NixOS module system allows you to create reusable configurations that can be imported across different deployment targets.

---

## Version Control and Maintenance

### Git LFS for Binary Fixtures
- Store small text-based test data directly in Git
- Use Git LFS for media fixtures and larger Neo4j dumps to avoid repository bloat
- Keeps test data versioned alongside application code

### Automated Data Refreshes
- Schedule regular refreshes of test datasets from sanitized production snapshots
- Strip sensitive information and anonymize PII during refresh process
- Maintains compliance while keeping test data realistic

### CI/CD Integration
- Embed test data provisioning into CI/CD pipeline
- Automated tests run against known-good datasets
- Accelerates development cycles and catches bugs earlier

---

## Related Documentation

- **[ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md)** - Complete integrated stack architecture, performance characteristics, scaling strategies, and operational procedures

## References

- [Cloudflare R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [Google Cloud Storage Pricing](https://cloud.google.com/storage/pricing)
- [Oracle Cloud Object Storage Pricing](https://www.oracle.com/cloud/storage/pricing/)
- [MinIO Documentation](https://min.io/docs/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Valkey Documentation](https://valkey.io/docs/)

