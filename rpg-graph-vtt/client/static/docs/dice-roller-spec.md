# Dice Roller System - Implementation-Agnostic Specification

**Version:** 1.0.0  
**Last Updated:** January 2025  
**Status:** MVP Complete - Production Ready

## 1. Executive Summary

This specification defines a deterministic 3D dice rolling system for the RPG Graph VTT platform. The system provides D&D Beyond–inspired dice animations with server-authoritative roll support, ensuring fairness and anti-cheat capabilities. The specification is implementation-agnostic, allowing deployment across different technology stacks (Python/FastAPI, Elixir/Phoenix, Go, etc.) while maintaining consistent behavior and data contracts.

### Core Principles

| Principle                  | Implementation                                                                 |
|----------------------------|---------------------------------------------------------------------------------|
| Deterministic Outcome      | Animation never decides the result — result is known before animation starts  |
| Server-Authoritative Ready | rollTo() accepts pre-calculated numbers from backend (or client RNG)          |
| Zero Asset Loading         | All dice are procedurally generated — instant load, no textures in MVP        |
| Mobile-First Performance   | < 150 KB total, 60 FPS on iPhone 12+, touch + mouse support                    |
| Chaos-Resilient            | Survives spam clicks, delayed resolves, resize/orientation changes            |
| Infrastructure-Aware       | Spec acknowledges Neo4j/Valkey constraints while remaining framework-neutral  |

## 2. System Architecture Layer

### High-Level Architecture

```
┌─────────────────┐
│   Web Client    │
│  (UI Component) │
└────────┬────────┘
         │ HTTP/WebSocket
         │
┌────────▼────────┐      ┌──────────────┐      ┌──────────────┐
│  API Gateway    │──────│  Roll Service│──────│    Neo4j     │
│  (HTTP Server)  │      │  (Business  │      │  (Graph DB)  │
└─────────────────┘      │   Logic)     │      └──────────────┘
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │    Valkey    │
                         │   (Cache)    │
                         └──────────────┘
```

### Component Boundaries

- **Web Client**: UI component that renders dice animations (framework-agnostic)
- **API Gateway**: HTTP endpoints for roll requests (FastAPI, Phoenix, Gin, etc.)
- **Roll Service**: Business logic for roll calculation and persistence
- **Neo4j**: Graph database for persistent roll history and character relationships
- **Valkey**: Cache layer for hot-path data and session state

### Protocols

- **REST API**: JSON over HTTP for roll requests
- **Bolt Protocol**: Neo4j connection (standard Bolt protocol)
- **Redis Protocol**: Valkey connection (Redis 7.x compatible)

## 3. Infrastructure Layer

### Required Infrastructure

- **Neo4j** (5.x+, Bolt protocol) - Graph database for character relationships and roll history
- **Valkey** (Redis 7.x compatible protocol) - Cache layer for sessions and hot-path data

### Graph Store Contract (Neo4j)

**Purpose**: Entity relationships, traversals, pattern matching for RPG data

**Query Language**: Cypher

**Schema**: 
- Node labels: `Character`, `DiceRoll`, `RollResult`, `Party`
- Relationship types: `MADE_ROLL`, `HAS_RESULT`, `BELONGS_TO_PARTY`
- See `neo4j-dice-schema.md` for complete schema definition

**Access Patterns**:
- Character lookups by UUID
- Roll history queries (recent rolls, by character, by party)
- Roll statistics (averages, critical hits, etc.)

**Connection**: Standard Bolt protocol (works with neo4j-driver, bolt_sips, go-neo4j, etc.)

**Free Tier Constraints**: Single database, limited resources, no clustering (design for scalability despite constraints)

### Cache Store Contract (Valkey)

**Purpose**: Session data, rate limiting, hot-path data, recent roll history

**Protocol**: Redis-compatible (Valkey uses Redis protocol)

**Data Structures**: 
- Strings: Rate limit counters
- Hashes: Character data, session state, roll results
- Sorted Sets: Roll history (sorted by timestamp)

**TTL Strategy**: 
- Character data: 1 hour
- Recent roll history: 1 hour
- Session state: 24 hours
- Rate limit counters: 1 minute

**Key Patterns**: 
- `rpg:character:{uuid}` - Character data
- `rpg:character:{uuid}:rolls` - Roll history (ZSET)
- `rpg:session:{id}` - Session state
- `rpg:ratelimit:{endpoint}:{ip}` - Rate limit counter
- `rpg:roll:{roll_uuid}` - Individual roll result

**Compatibility**: Works with redis-py, go-redis, redix (Elixir), etc.

See `valkey-cache-strategy.md` for complete cache strategy.

### Connection Management Standards

- **Connection Pooling**: Min 2, max 10 connections per service
- **Retry/Circuit Breaker**: Exponential backoff (100ms, 200ms, 400ms), max 3 retries
- **Health Checks**: Ping endpoints every 30 seconds, connection validation on startup
- **Credential Management**: Environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)

## 4. Data Architecture

### Neo4j Graph Schema

**Node Types**:
- `DiceRoll`: Complete roll event (notation, timestamp, context, total)
- `RollResult`: Individual die result (die_type, value, modifier)

**Relationship Types**:
- `(:Character)-[:MADE_ROLL]->(:DiceRoll)`
- `(:DiceRoll)-[:HAS_RESULT]->(:RollResult)`

**Indexes**:
- `dice_roll_timestamp` - For time-ordered queries
- `dice_roll_character` - For character roll lookups
- `roll_result_value` - For statistics queries

**Common Query Patterns**: See `neo4j-dice-schema.md` for complete Cypher examples.

### Valkey Cache Strategy

**What Gets Cached**:
- Character data (TTL: 1 hour)
- Recent roll results (TTL: 1 hour, last 50 rolls per character)
- Session state (TTL: 24 hours)
- Rate limit counters (TTL: 1 minute)

**Cache Key Structure**: Namespaced with `rpg:` prefix

**Invalidation Rules**:
- Character updates → invalidate character cache
- New roll → add to roll history cache, expire after TTL

**Consistency Requirements**: Eventual consistency acceptable for roll history, immediate for active sessions

See `valkey-cache-strategy.md` for complete strategy.

### State Management Strategy

- **Neo4j (Persistent)**: Character data, roll history, party relationships
- **Valkey (Ephemeral)**: Session state, recent rolls cache, rate limits
- **Memory (Transient)**: Active dice roll animations, UI state

## 5. API Contracts

### Roll Request Endpoint

**Endpoint**: `POST /api/rolls`

**Request Schema** (JSON):
```json
{
  "character_uuid": "string (UUID)",
  "notation": "string (dice notation, e.g., '1d20+5')",
  "context": "string (optional, e.g., 'Strength Check')",
  "server_authoritative": "boolean (optional, default: false)"
}
```

**Response Schema** (JSON):
```json
{
  "roll_uuid": "string (UUID)",
  "notation": "string",
  "results": [
    {
      "die_type": "string (d4, d6, d8, d10, d12, d20)",
      "value": "integer (face value)",
      "modifier": "integer",
      "total": "integer"
    }
  ],
  "total": "integer (sum of all results + modifiers)",
  "timestamp": "string (ISO 8601 datetime)",
  "context": "string"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid notation or missing required fields
- `401 Unauthorized`: Invalid or missing authentication
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Get Roll History Endpoint

**Endpoint**: `GET /api/characters/{character_uuid}/rolls?limit=10&offset=0`

**Response Schema** (JSON):
```json
{
  "rolls": [
    {
      "roll_uuid": "string",
      "notation": "string",
      "total": "integer",
      "timestamp": "string",
      "context": "string"
    }
  ],
  "total": "integer (total count)",
  "limit": "integer",
  "offset": "integer"
}
```

### Authentication Requirements

- JWT token in `Authorization: Bearer <token>` header
- Token validation on all roll endpoints
- Session-based authentication for web clients

### Error Codes

| Code | Meaning | Retryable |
|------|---------|-----------|
| 400 | Bad Request (invalid notation) | No |
| 401 | Unauthorized | No |
| 429 | Rate Limit Exceeded | Yes (with backoff) |
| 500 | Internal Server Error | Yes |
| 503 | Service Unavailable | Yes |

### Versioning

- API version in URL: `/api/v1/rolls`
- Version header: `X-API-Version: 1.0`
- Backward compatibility maintained for at least 2 major versions

## 6. Domain Model

### Core Entities

**DiceRoll**
- `uuid`: Unique identifier
- `notation`: Dice notation string
- `timestamp`: When roll occurred
- `context`: Roll context (ability check, attack, etc.)
- `character_uuid`: Character who made the roll
- `total`: Final calculated total

**RollResult**
- `uuid`: Unique identifier
- `die_type`: Type of die (d4-d20)
- `value`: Face value (1 to max for die type)
- `modifier`: Modifier applied
- `total`: value + modifier

**Character** (existing entity)
- Links to rolls via `MADE_ROLL` relationship
- Provides ability modifiers for roll calculations

### Relationships

- `Character` → `MADE_ROLL` → `DiceRoll`
- `DiceRoll` → `HAS_RESULT` → `RollResult`
- `Character` → `BELONGS_TO_PARTY` → `Party`

### State Transitions

1. **Roll Initiated**: User clicks roll button → API request created
2. **Roll Calculated**: Server generates results (or uses client RNG if not server-authoritative)
3. **Roll Persisted**: Results saved to Neo4j, cached in Valkey
4. **Roll Animated**: Client receives results, animates dice to target faces
5. **Roll Complete**: Animation finishes, results displayed

### Data Shapes (JSON Schema)

See API Contracts section for request/response schemas. All data uses JSON format for API communication.

## 7. Component Specifications

### Dice Visualizer Component

**Responsibilities**:
- Render 3D dice animations using WebGL
- Accept pre-calculated roll results
- Animate dice to target faces deterministically
- Emit events for roll start/complete

**Inputs**:
- Container element (HTML element or selector)
- Roll requests: `Array<{dieType: string, faceValue: number, modifier?: number}>`
- Options: `{theme?: string, cameraDistance?: number, animationDuration?: {min: number, max: number}}`

**Outputs**:
- Promise resolving to roll results array
- Events: `start`, `complete`

**Key Behaviors**:
- State lock prevents overlapping animations (`isRolling` flag)
- Handles window resize and orientation changes gracefully
- Supports zero-duration instant snap for testing
- Cleans up resources on destroy

**Framework-Neutral Interface**:
```typescript
interface DiceVisualizer {
  constructor(container: HTMLElement, options?: DiceOptions)
  roll(rollRequests: RollRequest[]): Promise<RollResult[]>
  rollTo(faceValues: number[], dieTypes: string[]): Promise<void>
  clearTray(): void
  setTheme(theme: string): void
  destroy(): void
  on(event: 'start' | 'complete', callback: Function): void
}
```

### Dice Logic Component

**Responsibilities**:
- Parse dice notation strings (e.g., "1d20+5", "2d6+3")
- Generate random roll results (or accept pre-determined)
- Convert between notation and visualizer format

**Inputs**:
- Dice notation string
- Optional: Pre-determined face values (for server-authoritative)

**Outputs**:
- Parsed notation object
- Roll result with individual dice and totals

**Key Behaviors**:
- Validates notation format
- Supports standard polyhedral dice (d4-d20)
- Handles modifiers (positive and negative)
- Can work with custom RNG function

### API Gateway Component

**Responsibilities**:
- Accept HTTP roll requests
- Validate authentication and input
- Route to roll service
- Return formatted responses

**Inputs**: HTTP POST request with JSON body

**Outputs**: HTTP response with JSON body

**Key Behaviors**:
- Rate limiting (per IP, per user)
- Input validation
- Error handling and formatting
- CORS support for web clients

### Roll Service Component

**Responsibilities**:
- Calculate roll results (or accept server-authoritative results)
- Persist rolls to Neo4j
- Cache rolls in Valkey
- Handle business logic (critical hits, advantage/disadvantage, etc.)

**Inputs**: Roll request with character context

**Outputs**: Roll result with all dice values

**Key Behaviors**:
- Server-authoritative mode: Generate results server-side
- Client-authoritative mode: Accept client-generated results, validate
- Persist to Neo4j with relationships
- Cache in Valkey for fast retrieval

## 8. Quality Attributes

### Performance Targets

- **Animation**: Completes in 1.2-2.0 seconds, maintains 60 FPS
- **API Response**: < 200ms for 95th percentile (excluding animation)
- **Database**: Roll persistence to Neo4j < 50ms
- **Cache**: Cache hit rate > 80% for character data
- **Bundle Size**: < 150 KB total (Three.js + code)
- **Load Time**: < 500ms initial render

### Security Requirements

- **Server-Authoritative Rolls**: Prevent client manipulation of results
- **Authentication**: All roll endpoints require valid JWT token
- **Rate Limiting**: Prevent abuse (e.g., 100 rolls/minute per user)
- **Input Validation**: Sanitize and validate all dice notation input
- **CORS**: Restrict to allowed origins

### Scalability Needs

- **Concurrent Rolls**: Support 20 concurrent dice without degradation
- **Roll History**: Efficiently query last 1000 rolls per character
- **Cache Scaling**: Valkey can scale horizontally (Redis Cluster)
- **Database Scaling**: Neo4j can scale vertically (or use Aura for horizontal)

### Accessibility

- **Keyboard Navigation**: All controls accessible via keyboard
- **Screen Reader Support**: ARIA labels on all interactive elements
- **Reduced Motion**: Respect `prefers-reduced-motion` media query
- **Touch Support**: Minimum 44px touch targets on mobile

### Data Consistency

- **Roll Results**: Persisted to Neo4j, cached in Valkey for 1 hour
- **Character Data**: Eventual consistency acceptable (1 hour TTL)
- **Session State**: Immediate consistency required
- **Roll History**: Eventual consistency acceptable

## 9. Chaos Engineering Tests

All tests must pass before production deployment:

| Test Name                  | Trigger Condition                                  | Expected Behavior                                      |
|----------------------------|----------------------------------------------------|--------------------------------------------------------|
| Rapid-Fire Stress          | 100 rolls in < 2 seconds                          | Only last roll animates, no glitches, no memory leak |
| Delayed Resolution         | Call roll(), resolve after 8 seconds               | Shows "tumbling" placeholder animation                 |
| Resize Mid-Roll            | window.resizeTo during animation                   | Renderer resizes instantly, dice stay in view          |
| Orientation Change (mobile)| rotate device mid-roll                             | Canvas resizes, animation continues uninterrupted     |
| Zero-Duration Snap         | roll(..., { duration: 0 })                         | Instantly snaps to result, no animation loop           |
| Concurrent Mixed Rolls     | 10d20 + 5d6 + 2d4 simultaneously                   | All dice animate cleanly, 60 FPS maintained            |

## 10. Future-Proof Upgrade Path

| Feature                  | How to upgrade later                              |
|--------------------------|----------------------------------------------------|
| True physics             | Replace tween loop with Cannon-es + worker        |
| Textured dice            | Swap MeshNormalMaterial → MeshStandardMaterial + GLTF loader |
| Sound effects            | Add Howler.js on 'complete' event                  |
| Multiplayer sync         | Broadcast outcome via Socket.io → all clients call rollTo() |
| Advantage/Disadvantage   | Roll 2d20, visualize both, highlight kept die     |

## 11. Implementation Notes

### Demo vs Production Marking

**Demo Scaffolding** (Python/FastAPI prototype):
- Quick implementation for validation
- May have rough error handling
- API contracts are production-ready

**Production-Ready Contracts**:
- OpenAPI specification (can generate clients in any language)
- JSON Schema for all data models
- Neo4j schema and Cypher queries
- Valkey cache key patterns

**Goal**: Team can implement in Elixir/Phoenix or Go using only this spec, without understanding Python prototype.

### Framework-Neutral Terminology

- "UI Component" not "React Component"
- "HTTP Endpoint" not "FastAPI Route"
- "Web Client" not "React App"
- "API Gateway" not "FastAPI Server"

### What to Avoid in Implementation

- Don't lock into framework-specific patterns
- Don't create framework-specific diagrams
- Don't mandate specific libraries (except infrastructure: Neo4j, Valkey)
- Don't specify implementation details unless non-negotiable

## 12. References

- Neo4j Schema: `neo4j-dice-schema.md`
- Valkey Cache Strategy: `valkey-cache-strategy.md`
- Dice Visualizer API: See Component Specifications section
- Chaos Engineering Tests: See Chaos Engineering Tests section

## 13. Version History

- **1.0.0** (January 2025): Initial MVP specification
  - Deterministic dice rolling
  - Neo4j persistence
  - Valkey caching
  - Chaos engineering tests
  - Character sheet integration

