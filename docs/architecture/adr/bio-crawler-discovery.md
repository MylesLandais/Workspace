# Bio-Crawler Discovery Logic

## Status

Accepted

## Context

Manually adding all handles for a creator across platforms is tedious and error-prone. Creators often link their other social accounts in their bios/About pages.

## Decision

Implement automated "Bio-Crawler" that scans anchor URLs (e.g., YouTube About page) for links to other platforms, discovering candidate handles automatically.

## Rationale

**Efficiency**: Reduces manual entry from hours to minutes for multi-platform creators.

**Completeness**: Discovers handles users might miss (e.g., TikTok account linked in YouTube bio).

**User Experience**: Wizard-style UI allows review and confirmation before importing.

**Auditability**: `[:REFERENCES]` edges track discovery path for verification.

## Implementation

### Discovery Process

1. User provides anchor URL (e.g., YouTube About page)
2. System fetches and parses HTML
3. Regex/heuristic matching for platform patterns:
   - Instagram: `instagram.com/[username]`
   - TikTok: `tiktok.com/@[username]`
   - Reddit: `reddit.com/r/[subreddit]` or `reddit.com/user/[username]`
   - Twitter: `twitter.com/[username]` or `x.com/[username]`
4. Create candidate Handle nodes with `verified: false`
5. Create `[:REFERENCES]` edges from anchor Handle to discovered Handles
6. Return candidate list for user review

### Neo4j Pattern

```cypher
// Anchor handle (where we started)
MATCH (anchor:Handle {id: $anchorId})

// Discovered candidate handles
CREATE (candidate:Handle {
  id: randomUUID(),
  platform: $platform,
  username: $username,
  handle: $handle,
  verified: false,
  discoveredFrom: $anchorId
})

// Reference edge tracks discovery
CREATE (anchor)-[:REFERENCES {
  discoveredAt: datetime(),
  confidence: $confidence,
  sourceUrl: $sourceUrl
}]->(candidate)
```

### Confidence Levels

- **High**: Link found in official bio/About page
- **Medium**: Username matches exactly across platforms
- **Low**: Partial match or inferred connection

### Verification Workflow

1. System presents candidate handles to user
2. User can check/uncheck handles to confirm
3. Confirmed handles get `verified: true` and `[:OWNS_HANDLE]` relationship
4. Unchecked handles remain as `[:REFERENCES]` only (for audit trail)

## Consequences

**Positive**:
- Dramatically reduces manual work
- Discovers connections users might miss
- Maintains audit trail via reference edges
- Supports confidence scoring

**Negative**:
- Requires HTML parsing and pattern matching
- False positives possible (fan pages, similar usernames)
- Requires user review step (can't be fully automated)

**Neutral**:
- Can be disabled for manual-only workflows
- Reference edges preserve discovery history

## Alternatives Considered

**Manual Entry Only**: Rejected because it's too time-consuming for multi-platform creators.

**Fully Automated**: Rejected because false positives would pollute the graph and verification is essential.

## Implementation Notes

- Use established libraries for HTML parsing (e.g., Cheerio, BeautifulSoup)
- Cache parsed results to avoid repeated fetches
- Rate limit external requests to avoid blocking
- Store raw HTML snippets for audit/debugging
- Support multiple anchor URLs (start from any platform)

## References

- Web scraping best practices
- OSINT (Open Source Intelligence) techniques






