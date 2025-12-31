# Bunny GUI: Bun + Docker Deployment Guide

This guide explains how to run the Bunny GUI frontend using Bun and Docker with the mock data factory.

## Prerequisites

- Docker installed
- Bun runtime (or use the Docker image which includes Bun)

## Quick Start

### Using Docker (Recommended)

```bash
# Build Docker image
docker build -f Dockerfile.bun -t bunny-gui

# Run the container
docker run --rm -p 4321:4321 -v $(pwd):/app bunny-gui

# Stop the container (Ctrl+C or close terminal)
```

### Using Bun Locally

```bash
# Install dependencies
bun install

# Start development server
bun run dev

# Build for production
bun run build

# Preview production build
bun run preview
```

## Mock Data Factory

The application uses a mock data factory at [`src/lib/mock-data/factory.ts`](src/lib/mock-data/factory.ts) to provide:

### Available Entities (Persons/Actors)
- Taylor Swift
- Selena Gomez
- Brooke Monk
- Miss Katie
- Fasffy
- Sjokz

### Available Boards
- Pop Queenz ✨ (Taylor Swift + Selena Gomez)
- Linux Threads 🐧 (r/unixporn, r/kde, r/battlestations)
- Reader Inbox 📚 (Long-form articles)
- Marketplace 💰 (Items for sale and trade)

### Mock Data Features
- **Entity Management**: Create, update, delete entities with sources, relationships, and context keywords
- **Content Filtering**: Filter by persons, sources, tags, and search queries
- **View Modes**: Visual feed, Reader inbox, Archive
- **Standardized Validation**: Frontend validation at scale using identity lookup and search

## Environment Variables

The application reads from `.env` file in the project root:

```bash
# Enable mock data mode (uses mock factory instead of GraphQL)
BUN_USE_MOCK_DATA=true

# GraphQL endpoint (ignored in mock mode)
PUBLIC_GRAPHQL_ENDPOINT=http://localhost:4002/api/graphql
```

## Docker Configuration

### Dockerfile ([`Dockerfile.bun`](Dockerfile.bun))
- Uses official Bun image: `oven/bun:1.1-slim`
- Installs dependencies with `bun install`
- Exposes port 4321
- Runs `bun run dev --host` for development

### Docker Compose (Optional)
If you prefer using Docker Compose, you can use the following configuration:

```yaml
services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.bun
    ports:
      - "4321:4321"
    volumes:
      - .:/app
      - /app/node_modules
      - ../../temp:/app/public/temp:ro
    working_dir: /app
    env_file:
      - /home/warby/Workspace/Bunny/.env
    environment:
      - BUN_USE_MOCK_DATA=true
      - BUN_INSTALL_LOCKFILE_ONLY=true
      - NODE_ENV=development
    stdin_open: true
    tty: true
```

## Development Workflow

1. **Start with Mock Data**: The application runs in mock mode by default, using the mock data factory
2. **Entity Management**: Use EntityManagerView to create and manage entities
3. **Content Generation**: The mock factory generates dynamic content based on entity profiles
4. **Frontend Validation**: Use standardized validation methods for entity lookups and searches

## Switching to Real Backend

To switch from mock data to real GraphQL backend:

1. Set environment variable:
   ```bash
   BUN_USE_MOCK_DATA=false
   ```

2. Update GraphQL endpoint:
   ```bash
   PUBLIC_GRAPHQL_ENDPOINT=your-graphql-endpoint
   ```

3. The application will automatically use GraphQL queries instead of mock factory

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 4321
lsof -i :4321

# Kill the process if needed
kill -9 <PID>
```

### Docker Container Issues
```bash
# Rebuild the image
docker build -f Dockerfile.bun -t bunny-gui

# Run the container again
docker run --rm -p 4321:4321 -v $(pwd):/app bunny-gui
```

### Bun Dependencies
```bash
# Clear cache and reinstall
rm -rf node_modules bun.lock
bun install
```

## Project Structure

```
app/frontend/
├── src/
│   ├── components/
│   │   └── bunny/
│   │       ├── EntityManagerView.tsx    # Entity management with mock factory
│   │       ├── Sidebar.tsx              # Navigation sidebar
│   │       ├── FilterBar.tsx            # Filter chips
│   │       ├── FeedItem.tsx             # Feed cards
│   │       ├── Lightbox.tsx             # Full-screen viewer
│   │       └── BunnyFeed.tsx           # Main feed component
│   └── lib/
│       ├── bunny/
│       │   ├── types.ts                # Shared type definitions
│       │   └── services/
│       │       └── fixtures.ts           # Demo data
│       └── mock-data/
│           └── factory.ts              # Mock data factory
├── Dockerfile.bun                     # Bun Docker configuration
├── package.json                      # Dependencies and scripts
└── README-BUN-DOCKER.md            # This file
```

## Next Steps

1. ✅ Mock Data Factory - Complete with entity registry
2. ✅ Bun + Docker Configuration - Ready for deployment
3. ⏳ Entity Management View - Using mock factory
4. ⏳ Global Sidebar Integration - Unified navigation
5. ⏳ Visual/Reader Mode Toggle - Hybrid content support
6. ⏳ Real Backend Integration - GraphQL client when ready

## Support

For issues or questions about Bunny GUI setup:
- Check [Mock Data Factory documentation](src/lib/mock-data/factory.ts)
- Review [Entity Management View](src/components/bunny/EntityManagerView.tsx)
- See [Project Plans](../plans/) for architecture decisions
