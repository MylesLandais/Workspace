# Data Sources for Entity Profiles

Documentation of external data sources used to enrich creator/entity profiles.

## Primary Sources

### Wikipedia

**URL Pattern**: `https://en.wikipedia.org/wiki/{name}`

**Data Available**:
- Birth date and place
- Nationality
- Occupation(s)
- Education
- Employer(s)
- Career highlights
- Height (if available)
- Awards and recognition

**Extraction Method**:
- Parse Wikipedia infobox template
- Use structured data from infobox person template
- Fallback to article text parsing if infobox missing

**Confidence**: High (curated, verified content)

**Example**:
```
Name: Eefje Depoortere
Birth Date: June 16, 1987
Birth Place: Bruges, Belgium
Occupation: Television presenter, reporter, esports player
Education: Ghent University
Employer: Riot Games, Electronic Sports League
Height: 1.73 m
```

**Crawling Notes**:
- Respect Wikipedia's robots.txt
- Use API when possible (MediaWiki API)
- Cache results (Wikipedia updates infrequently)
- Handle redirects and disambiguation pages

---

### Instagram

**URL Pattern**: `https://www.instagram.com/{username}/`

**Data Available**:
- Follower count
- Following count
- Post count
- Bio/description
- Profile picture
- Recent posts (for content analysis)
- Verified status

**Extraction Method**:
- Instagram Graph API (requires authentication)
- Or HTML parsing (less reliable, may break)
- Extract from profile page metadata

**Confidence**: High (official platform data)

**Example**:
```
Username: @eefjah
Followers: 548,300
Bio: "Host & producer - Berlin but Masters in History & Journalism"
Verified: true
```

**Crawling Notes**:
- Requires API access or careful HTML parsing
- Rate limits apply
- Real-time data (changes frequently)
- Profile may be private (handle gracefully)

---

### YouTube

**URL Pattern**: `https://www.youtube.com/@{handle}` or `https://www.youtube.com/c/{name}`

**Data Available**:
- Subscriber count
- Total video count
- Channel description
- Channel banner/avatar
- Recent videos
- Channel creation date

**Extraction Method**:
- YouTube Data API v3
- Or HTML parsing (channel page)

**Confidence**: High (official platform data)

**Crawling Notes**:
- API requires authentication
- Quota limits apply
- Real-time subscriber counts

---

## Secondary Sources

### WikiFeet

**URL Pattern**: `https://wikifeet.com/{Name}`

**Data Available**:
- Birth date
- Birthplace
- Height
- Shoe size
- Physical measurements
- Rating/score (user-contributed)

**Extraction Method**:
- HTML parsing (structured profile page)
- Extract from profile information section

**Confidence**: Medium (user-contributed, may have inaccuracies)

**Example**:
```
Birth date: 2003-01-31
Birthplace: United States
Height: 5 ft 5 in
Shoe size: 6.5 US
```

**Crawling Notes**:
- User-contributed content (verify against other sources)
- Use as supplementary data only
- May not exist for all creators
- Handle NSFW content appropriately

---

### Google Knowledge Panel

**URL Pattern**: Search result (not directly crawlable)

**Data Available**:
- Aggregated stats
- Quick facts
- Related people
- Social media links
- Recent activity

**Extraction Method**:
- Not directly crawlable (Google search result)
- Can use Google Knowledge Graph API if available
- Or scrape search results (fragile, may break)

**Confidence**: Medium (aggregated, may have errors)

**Crawling Notes**:
- Google's Knowledge Graph API requires API key
- Search result scraping is fragile
- Use as validation/supplement only

---

## Data Source Priority

When multiple sources provide conflicting data:

1. **Wikipedia** (highest priority)
   - Curated, verified
   - Structured infobox format
   - Community-maintained accuracy

2. **Official Platform APIs** (high priority)
   - Instagram, YouTube, Twitter official APIs
   - Real-time, authoritative
   - Platform-specific data

3. **Platform HTML Parsing** (medium priority)
   - When API not available
   - More fragile, may break

4. **Specialized Sites** (low priority)
   - WikiFeet, IMDb, etc.
   - Use for supplementary data only
   - Verify against primary sources

## Conflict Resolution

When sources conflict:

1. **Birth Date**: Prefer Wikipedia, then official platforms
2. **Height**: Prefer Wikipedia, then specialized sites (WikiFeet)
3. **Follower Counts**: Use platform APIs (most current)
4. **Bio**: Prefer official platform bios, then Wikipedia

Track conflicts in metadata:
```cypher
CREATE (c:Creator)-[:METADATA_CONFLICT {
  field: "height",
  source1: "wikipedia",
  value1: "1.73 m",
  source2: "wikifeet",
  value2: "5'8\"",
  resolved: false
}]->(c)
```

## Implementation Example

```cypher
// Create creator with Wikipedia data
CREATE (c:Creator {
  id: "sjokz",
  name: "Eefje Depoortere",
  displayName: "Sjokz",
  birthDate: date("1987-06-16"),
  birthPlace: "Bruges, Belgium",
  nationality: "Belgian",
  height: "1.73 m",
  heightCm: 173,
  occupation: ["Television presenter", "Reporter", "Esports player"],
  employer: ["Riot Games", "Electronic Sports League"],
  education: ["Ghent University"],
  dataSources: ["wikipedia"]
})

// Add Instagram data
MATCH (c:Creator {id: "sjokz"})
SET c.instagramFollowers = 548300,
    c.instagramBio = "Host & producer - Berlin but Masters in History & Journalism",
    c.dataSources = c.dataSources + ["instagram"]
```

## Crawling Strategy

1. **Initial Profile Creation**:
   - User provides name or URL
   - System searches Wikipedia
   - Extract infobox data
   - Create Creator node

2. **Platform Discovery**:
   - Bio-crawler finds platform links
   - Extract platform-specific data
   - Update Creator with platform stats

3. **Enrichment**:
   - Periodically crawl specialized sites
   - Update missing fields
   - Resolve conflicts

4. **Maintenance**:
   - Re-crawl high-value sources (Wikipedia, platforms)
   - Update follower counts regularly
   - Flag stale data

## References

- Wikipedia: https://en.wikipedia.org/wiki/Template:Infobox_person
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api
- YouTube Data API: https://developers.google.com/youtube/v3
- Google Knowledge Graph API: https://developers.google.com/knowledge-graph


