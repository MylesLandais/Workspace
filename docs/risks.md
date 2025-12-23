# Risk Tracking

This document tracks known risks that may impact system stability, data quality, or user experience.

## External Dependencies

### Reddit API Rate Limiting / Blocking

**Risk Level**: High  
**Impact**: Complete service disruption  
**Probability**: Medium

**Description**: Reddit may rate limit or block our API requests if we exceed their limits or violate their terms of service.

**Mitigation**:
- Implement exponential backoff for API requests
- Respect rate limit headers from Reddit API
- Use multiple API keys/accounts if needed (within ToS)
- Cache responses aggressively
- Monitor request patterns and adjust accordingly

**Detection**: 
- Track 429 (Too Many Requests) responses
- Monitor success rate of API calls
- Alert on consecutive failures

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
**Impact**: Slow frontend, poor UX  
**Probability**: Medium

**Description**: Complex GraphQL queries may become slow as data volume grows.

**Mitigation**:
- Query complexity analysis
- Database indexes on frequently queried fields
- Pagination for all list queries
- Query result caching
- Performance monitoring and alerting

**Detection**:
- Track query execution times
- Monitor Apollo Client cache hit rates
- User-reported slow performance

**Status**: Active monitoring

---

## Operational

### Ingestion Worker Failures

**Risk Level**: Medium  
**Impact**: Stale data, missed content  
**Probability**: Low

**Description**: Background workers that fetch and ingest content may crash or fail silently.

**Mitigation**:
- Worker health monitoring
- Automatic restart on failure
- Dead letter queue for failed jobs
- Status Pulse indicator for visibility
- Alert on worker downtime

**Detection**:
- Last sync timestamp monitoring
- Worker heartbeat/health checks
- Alert when sync age exceeds threshold

**Status**: Active monitoring

---

## Review Process

This document should be reviewed:
- Monthly for risk assessment updates
- After any incident to add new risks
- When new features are added that introduce dependencies
- When external service changes are announced

## Risk Levels

- **High**: Could cause complete service disruption or data loss
- **Medium**: Could significantly impact user experience or require manual intervention
- **Low**: Minor impact, easily recoverable


