# Feed Manager Client

Astro frontend for the Fjord Control feed management system.

## Development with Docker

This project uses Docker for development to avoid installing packages on the host system.

### Prerequisites

- Docker
- Docker Compose

### Getting Started

1. Build and start the development server:

```bash
docker-compose up --build
```

2. Open your browser to `http://localhost:4321`

The dev server will hot-reload on file changes.

### Testing

Run tests inside the Docker container:

```bash
# Run all tests
docker-compose exec frontend bun run test

# Run tests in watch mode
docker-compose exec frontend bun run test:watch

# Run tests with coverage
docker-compose exec frontend bun run test:coverage

# Run tests with UI
docker-compose exec frontend bun run test:ui
```

Or run tests locally (if you have Bun installed):

```bash
bun run test
bun run test:watch
bun run test:coverage
```

### Test Structure

- Component tests: `src/components/**/__tests__/*.test.tsx`
- Utility tests: `src/lib/**/__tests__/*.test.ts`
- Test setup: `src/test/setup.ts`

### Project Structure

```
src/
├── components/     # React components (islands)
│   ├── feed/
│   ├── feed-manager/
│   └── admin/
├── layouts/        # Astro layouts
├── pages/          # Astro pages (routing)
├── lib/            # Utilities and helpers
└── test/           # Test utilities and setup
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `PUBLIC_GRAPHQL_ENDPOINT`: GraphQL API endpoint
- `PUBLIC_GRAPHQL_MOCK`: Enable MSW mocking (true/false)
- `PUBLIC_WS_ENDPOINT`: WebSocket endpoint for subscriptions

### Building for Production

```bash
docker-compose run --rm frontend bun run build
```

Output will be in `dist/`.
