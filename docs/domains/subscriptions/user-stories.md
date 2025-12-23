# User Story Cards

Product and engineering story cards for the Feed Manager system.

## Epic: The Entity Resolution Layer

### Card 1: GraphQL Schema Evolution (The Creator Node)

**As a** API Consumer (Frontend),

**I want** to query for a `Creator` entity that contains aggregated metadata (Name, Bio, Avatar),

**So that** I can display a unified profile header instead of a specific social media page.

**Acceptance Criteria:**
- Define `Creator` type in GraphQL schema
- Define `Handle` type (representing a specific account on a specific platform)
- Establish a `1:Many` relationship: A `Creator` has many `Handles`
- Query `creator(slug: "sjokz")` returns nested array of linked handles and their platforms

**Technical Notes:**
- Creator node holds canonical identity (real name, bio, avatar)
- Handle nodes hold platform-specific information
- GraphQL resolver traverses `Creator -> Handles` relationship

---

### Card 2: The "Bio-Crawler" Discovery Logic

**As a** System Administrator,

**I want** the backend to automatically scan a provided "Anchor URL" (e.g., a YouTube "About" page) for links to other social platforms,

**So that** we can identify a creator's entire digital footprint without manual entry.

**Acceptance Criteria:**
- System accepts an input URL
- System parses the external page for recognized patterns (Regex/Heuristic matching for Instagram, TikTok, Reddit, etc.)
- System returns a list of *Candidate Handles* found on that page
- Candidate Handles must be flagged as `unverified` until confirmed by the user or a secondary check

**Technical Notes:**
- Use HTML parsing library (Cheerio, BeautifulSoup)
- Pattern matching for common platform URL formats
- Create `[:REFERENCES]` edges for discovery audit trail
- Confidence scoring (high/medium/low) based on source location

---

### Card 3: Cross-Platform Media Normalization

**As a** Data Engineer,

**I want** to map disparate external API responses (Tweets, YouTube Videos, TikToks) into a single standard `Media` node structure,

**So that** the frontend can render a generic "Feed" without needing custom logic for every provider.

**Acceptance Criteria:**
- Define a standard `Media` interface (e.g., `title`, `source_url`, `publish_date`, `thumbnail`, `media_type`)
- Create adapters for each supported platform to map their specific JSON fields to this standard interface
- Ensure "Video Duration" and "Aspect Ratio" are standardized to support layout engines (masonry grids)

**Technical Notes:**
- Adapter pattern for each platform
- Store raw platform response in `rawData` for debugging
- Use Neo4j labels (`:Video`, `:Image`, `:Text`) for efficient querying
- Normalize duration to seconds, aspect ratio to string format

---

### Card 4: The Aggregated "Omni-Feed" Query

**As a** User,

**I want** to request a feed for "Brooke Monk" and receive a chronological mix of her TikToks, YouTube Shorts, and Instagram posts,

**So that** I don't have to switch tabs to see her latest content.

**Acceptance Criteria:**
- GraphQL Query `feed(creatorId: "...")` aggregates `Media` nodes from *all* connected `Handles`
- Support filtering arguments: `excludePlatforms: ["TikTok"]`
- Support sorting by `publishedAt` across different platforms (e.g., a Tweet from 5 mins ago appears above a YouTube video from 1 hour ago)

**Technical Notes:**
- Query traverses `Creator -> Handles -> Media` relationships
- Sort by `publishDate` descending
- Filter by platform if specified
- Cursor-based pagination for infinite scroll

---

## Epic: UI/UX & Workflows

### Card 5: The Identity Discovery Wizard (UI)

**As a** User,

**I want** a multi-step modal when adding a new tracked entity,

**So that** I can review and confirm the system's automated discoveries before importing data.

**Acceptance Criteria:**
- **Step 1:** Input field for Name or URL
- **Step 2:** "Disambiguation" state (if I type "Smith", show me which "Smith")
- **Step 3:** Visual feedback (spinner/progress) while the "Bio-Crawler" runs
- **Step 4:** A checklist of discovered handles. Allow the user to uncheck handles they believe are incorrect or irrelevant (e.g., "Ignore the fan-made Facebook page")

**Technical Notes:**
- Multi-step wizard component
- GraphQL mutation: `discoverHandles(anchorUrl: String!)`
- GraphQL mutation: `confirmDiscoveredHandles(creatorId: ID!, handleIds: [ID!]!)`
- Show confidence levels and source URLs for each candidate

---

### Card 6: Visual Source Attribution

**As a** User viewing the grid,

**I want** clear visual indicators on media cards showing which platform the content originated from,

**So that** I know if clicking the item will take me to YouTube, Reddit, or TikTok.

**Acceptance Criteria:**
- Each `Media` object in the API response includes a `platformIcon` or `platformName` field
- UI renders a high-contrast badge/icon on the media card
- Clicking the card opens the content in the most native format possible (embedded player vs. external link)

**Technical Notes:**
- Platform enum in GraphQL schema
- Platform-specific icons/assets
- Handle click routing based on platform (YouTube embed, Reddit link, etc.)

---

## Implementation Priority

1. **Card 1** (Creator Node) - Foundation for everything else
2. **Card 3** (Media Normalization) - Required for feed display
3. **Card 4** (Omni-Feed) - Core user value
4. **Card 2** (Bio-Crawler) - Efficiency improvement
5. **Card 5** (Discovery Wizard) - UX enhancement
6. **Card 6** (Visual Attribution) - Polish


