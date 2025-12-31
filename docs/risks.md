# Risk Tracking

This document tracks known risks that may impact system stability, data quality, or user experience. Risks are categorized by domain and include mitigation strategies, detection methods, and current status.

## External Dependencies

### Reddit Web Scraping Rate Limiting and Blocking

**Risk Level**: High  
**Impact**: Complete service disruption for Reddit-based ingestion  
**Probability**: Medium

**Description**: Reddit may rate limit or block web scraping requests if we exceed their limits or violate their terms of service. Since we use web scraping (not the official API), we're more vulnerable to blocking.

**Mitigation**:
- Implement exponential backoff with jitter for requests
- Respect robots.txt and rate limit headers
- Use rotating user agents and IP addresses (within ToS)
- Cache responses aggressively to minimize requests
- Monitor request patterns and adjust rate limits dynamically
- Implement circuit breaker pattern for failed requests

**Detection**:
- Track HTTP status codes (429, 403, 503)
- Monitor success rate of scraping requests
- Alert on consecutive failures or pattern changes
- Track response time degradation

**Status**: Active monitoring

---

### Subreddit Bans or Deletions

**Risk Level**: Medium  
**Impact**: Data source loss, user confusion  
**Probability**: Medium

**Description**: A subreddit we're ingesting from may be banned, set to private, or deleted by Reddit admins.

**Mitigation**:
- Health checks that verify subreddit accessibility
- Graceful degradation: mark source as unavailable, don't crash
- User notification when a subscribed subreddit becomes unavailable
- Archive existing data even if source is lost

**Detection**:
- Monitor 403/404 responses from subreddit endpoints
- Check subreddit metadata (subscriber count, description) for changes
- Alert when subreddit status changes

**Status**: Active monitoring

---

### Reddit API Changes

**Risk Level**: Medium  
**Impact**: Breaking changes to ingestion pipeline  
**Probability**: Low

**Description**: Reddit may deprecate or change their API endpoints, response formats, or authentication methods.

**Mitigation**:
- Version pinning where possible
- Abstract API client layer for easy updates
- Monitor Reddit developer announcements
- Maintain fallback parsing strategies

**Detection**:
- Automated tests that verify API contract
- Monitor for unexpected response format changes
- Track API version deprecation notices

**Status**: Active monitoring

---

## Data Quality

### Low-Quality Content Ingestion

**Risk Level**: Low  
**Impact**: Poor user experience, storage waste  
**Probability**: High

**Description**: Ingested content may not meet quality thresholds (low resolution, spam, off-topic).

**Mitigation**:
- IngestRule filters (minScore, mediaOnly, resolution checks)
- Trash Review interface for manual quality control
- Automated content analysis where possible
- User feedback mechanisms

**Detection**:
- Track rejection rates by rule
- Monitor user engagement metrics
- Review Trash Review queue regularly

**Status**: Active monitoring

---

### Duplicate Content

**Risk Level**: Low  
**Impact**: Redundant data, poor UX  
**Probability**: Medium

**Description**: Same image/post may be ingested multiple times from different sources or reposts.

**Mitigation**:
- Content deduplication by image hash/URL
- Unique constraints on Post.id (Reddit post ID)
- Cross-reference checks before ingestion

**Detection**:
- Monitor duplicate detection rates
- User reports of duplicate content

**Status**: Active monitoring

---

## Infrastructure

### Neo4j Connection Failures

**Risk Level**: High  
**Impact**: Complete service disruption  
**Probability**: Low

**Description**: Database connection issues, network partitions, or Neo4j service outages.

**Mitigation**:
- Connection pooling with retry logic
- Health check endpoints
- Graceful error handling in all database operations
- Consider read replicas for high availability

**Detection**:
- Database health monitoring
- Alert on connection failure rates
- Track query timeouts

**Status**: Active monitoring

---

### GraphQL API Performance Degradation

**Risk Level**: Medium  
**Impact**: Slow frontend, poor user experience  
**Probability**: Medium

**Description**: Complex GraphQL queries may become slow as data volume grows. N+1 query problems, missing indexes, or inefficient Cypher queries can cause significant performance degradation.

**Mitigation**:
- Query complexity analysis and limits
- Database indexes on frequently queried fields (userId, publishDate, platform)
- Cursor-based pagination for all list queries
- Valkey query result caching (300s TTL for feed queries)
- Performance monitoring and alerting (p95, p99 latency)
- Query batching and data loader patterns
- Neo4j query plan analysis for optimization

**Detection**:
- Track query execution times (p50, p95, p99)
- Monitor Valkey cache hit rates
- GraphQL query complexity metrics
- User-reported slow performance
- Neo4j slow query logging

**Status**: Active monitoring

---

## Operational

### Ingestion Worker Failures

**Risk Level**: Medium  
**Impact**: Stale data, missed content  
**Probability**: Low

**Description**: Background workers that fetch and ingest content may crash, fail silently, or become unresponsive. This leads to outdated feeds and missed content.

**Mitigation**:
- Worker health monitoring with heartbeat mechanism
- Automatic restart on failure with exponential backoff
- Dead letter queue for failed jobs with retry logic
- Pipeline status endpoint for visibility
- Alert on worker downtime or extended sync delays
- Graceful shutdown handling
- Queue-based job processing (Valkey queues)

**Detection**:
- Last sync timestamp monitoring per handle
- Worker heartbeat/health checks every 30 seconds
- Alert when sync age exceeds threshold (e.g., 1 hour)
- Track job failure rates and error types
- Monitor queue depth and processing rate

**Status**: Active monitoring

---

### Valkey Cache Failures

**Risk Level**: Medium  
**Impact**: Performance degradation, increased database load  
**Probability**: Low

**Description**: Valkey cache service may fail, causing all queries to hit Neo4j directly. This can cause significant performance degradation and increased database load.

**Mitigation**:
- Graceful degradation: system continues to function without cache
- Health check endpoints for cache connectivity
- Automatic failover to direct Neo4j queries
- Cache warming on service restart
- Monitor cache memory usage and eviction rates

**Detection**:
- Cache connection health monitoring
- Track cache hit rate (alert if < 70%)
- Monitor Neo4j query load increase
- Alert on cache service unavailability

**Status**: Active monitoring

---

### Neo4j Aura Tier Limits

**Risk Level**: Medium  
**Impact**: Service throttling, read-only mode, potential data loss  
**Probability**: Medium

**Description**: Exceeding Neo4j Aura free tier limits (operations, storage) can cause service throttling or read-only mode. In extreme cases, data may be at risk.

**Mitigation**:
- Monitor Aura usage metrics (operations, storage)
- Implement data archival strategies for old content
- Optimize queries to reduce operation count
- Use Valkey to offload hot data from Neo4j
- Set up alerts before reaching tier limits
- Plan for tier upgrades before limits are reached

**Detection**:
- Daily monitoring of Aura usage dashboard
- Alert at 80% of tier limits
- Track operation count trends
- Monitor storage growth rate

**Status**: Active monitoring

---

### Image Storage Costs

**Risk Level**: Low  
**Impact**: Increased infrastructure costs  
**Probability**: High

**Description**: As image content grows, S3-compatible storage costs can increase significantly. Without optimization, costs can scale linearly with content volume.

**Mitigation**:
- Implement image compression and optimization
- Use appropriate storage tiers (hot, warm, cold)
- Lifecycle policies for old content (archive after 90 days)
- Deduplication to prevent storing identical images
- Monitor storage usage and costs
- Set up cost alerts

**Detection**:
- Monthly storage usage and cost reports
- Alert on cost threshold increases
- Track storage growth rate
- Monitor deduplication effectiveness

**Status**: Active monitoring

---

## Review Process

This document should be reviewed:

- **Monthly**: Risk assessment updates and status reviews
- **After incidents**: Add new risks identified during incidents
- **Feature additions**: Review risks when new features introduce dependencies
- **External changes**: Update when external services announce changes
- **Quarterly**: Comprehensive risk review and mitigation effectiveness assessment

## Risk Levels

- **High**: Could cause complete service disruption or data loss. Requires immediate attention and mitigation.
- **Medium**: Could significantly impact user experience or require manual intervention. Should be monitored closely.
- **Low**: Minor impact, easily recoverable. Tracked for awareness but not critical path.






