# Media Platform

Production-ready media platform with Neo4j graph database, Valkey cache layer, and S3-compatible object storage.

## Architecture

- **Neo4j** - Graph database for relationships and metadata
- **Valkey** - In-memory cache for performance optimization
- **MinIO/GCP/R2** - S3-compatible object storage for media files

See [docs/ARCHITECTURE_OVERVIEW.md](../docs/ARCHITECTURE_OVERVIEW.md) for complete architecture details.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- npm or yarn

### Setup

1. **Clone and navigate:**
   ```bash
   cd media-platform
   ```

2. **Copy environment file:**
   ```bash
   cp .env.local.example .env.local
   ```

3. **Start services:**
   ```bash
   npm run docker:up
   ```

4. **Install dependencies:**
   ```bash
   npm install
   ```

5. **Start the application:**
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:3000`

## Services

Once started, you'll have:

- **Application**: http://localhost:3000
- **Neo4j Browser**: http://localhost:7475
- **Neo4j Bolt**: bolt://localhost:7688
- **MinIO Console**: http://localhost:9001
- **MinIO API**: http://localhost:9000
- **Valkey**: localhost:6379

**Note**: Neo4j uses ports 7475 (HTTP) and 7688 (Bolt) to avoid conflicts with other Neo4j instances.

## Environment Configuration

The application supports multiple environments:

- **Local**: `.env.local` - Development with Docker services
- **Staging**: `.env.staging` - Staging with managed services
- **Production**: `.env.production` - Production configuration

Copy the appropriate `.env.*.example` file and fill in your credentials.

## API Endpoints

- `GET /health` - Health check with service status
- `GET /api/cache/stats` - Cache statistics
- `POST /api/cache/flush` - Flush cache (dev/staging only)
- `GET /api/media/:id` - Get media by ID
- `GET /api/media/:id/metadata` - Get media with metadata
- `GET /api/users/:userId/media` - List user's media
- `GET /api/collections/:id` - Get collection by ID

## Development

```bash
# Start services
npm run docker:up

# Run in development mode
npm run dev

# View logs
npm run docker:logs

# Stop services
npm run docker:down
```

## Testing

```bash
# Run tests
npm test

# Run integration tests
npm run test:integration
```

## Cache Management

```bash
# View cache statistics
npm run cache:stats

# Flush cache (dev/staging only)
npm run cache:flush
```

## Documentation

- [Architecture Overview](../docs/ARCHITECTURE_OVERVIEW.md) - Complete stack architecture
- [Infrastructure Decisions](../docs/INFRASTRUCTURE_DECISIONS.md) - Technology choices and rationale

## License

ISC

