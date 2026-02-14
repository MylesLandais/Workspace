# Docker Deployment Plan: TypeScript + Bun Migration

## Executive Summary

This plan outlines the migration to a comprehensive Docker-based development environment with TypeScript (strict mode) and Bun runtime, replacing the current npm/Node.js setup. The goal is to establish end-to-end type safety from Neo4j through Ash/GraphQL to TypeScript, while maintaining fast development cycles and proper Docker networking.

## Core Decisions

### TypeScript (Strict Mode) - Non-Negotiable

**Rationale:**
- Neo4j data is schemaless and graph-shaped (dynamic properties, nested relationships)
- Ash provides strongly-typed resources on backend
- AshGraphql exposes clean GraphQL API
- GraphQL Codegen → auto-generated TypeScript types = end-to-end type safety
- Prevents runtime errors when traversing relationships (e.g., `character.skills[0].damage` undefined)

### Bun Runtime - Preferred Over Node.js/Deno

**Rationale:**
- Native TypeScript support (no tsc step needed)
- 10-20x faster installs/builds vs npm/yarn
- Excellent Tailwind/PostCSS compatibility
- Perfect Phoenix asset pipeline integration
- Leaner Docker images than Node.js
- Works seamlessly with `crbelaus/bun` mix task

**Why Not Deno:**
- Less mature Phoenix integration
- Requires more configuration for Tailwind/PostCSS/esbuild
- No advantage over Bun for this use case

**Why Not Phoenix Defaults (esbuild wrapper):**
- We're using TS for config + potentially complex hooks
- Bun provides better DX (faster, native TS)
- Better for future complex client-side features

## Implementation Components

### 1. Docker Configuration

#### Files to Create

**docker-compose.yml**
- Neo4j service with health checks
- Phoenix app service with volume mounts
- Proper networking (service name resolution)
- Environment variable configuration
- Health check dependencies

**Dockerfile (Multi-stage)**
- Builder stage: Install Bun, compile assets
- Runtime stage: Minimal Alpine with Elixir/Erlang
- Clean separation of build vs runtime dependencies
- Remove node_modules after build (not needed in final image)

**.dockerignore**
- Exclude node_modules, _build, deps (rebuild in container)
- Exclude development-only files

#### Key Features

- Neo4j health checks ensure readiness before Phoenix starts
- Phoenix binds to `0.0.0.0` (already configured in `config/dev.exs`)
- Neo4j connection: `bolt://neo4j:7687` (Docker service name)
- Volume mounts for hot-reload development
- Support both Docker Compose (service names) and local dev (localhost)

### 2. TypeScript Migration

#### Files to Create/Modify

**assets/js/app.js → assets/js/app.ts**
- Convert existing JavaScript to TypeScript
- Add proper type annotations
- Declare modules for Phoenix libraries

**tsconfig.json**
- Strict mode enabled (`strict: true`)
- Target ES2017+ (Phoenix LiveView compatible)
- Proper module resolution
- Path aliases for clean imports

**Type Definitions**
- Declare modules for `phoenix`, `phoenix_html`, `phoenix_live_view`
- Create minimal type definitions if official ones unavailable
- Ensure compatibility with LiveView hooks

#### TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "module": "ES2020",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true
  },
  "include": ["js/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 3. Bun Integration

#### Package.json Updates

**Scripts:**
- `bun install` (replaces `npm install`)
- `bun run build` - Build assets for production
- `bun run watch` - Watch mode for development
- `bun run typecheck` - Type checking (CI/pre-commit)
- `bun run codegen` - Generate GraphQL types
- `bun run codegen:watch` - Watch mode for GraphQL codegen

**Dependencies:**
- Keep existing: `phoenix`, `phoenix_html`, `phoenix_live_view`, `topbar`
- Add GraphQL Codegen:
  - `@graphql-codegen/cli`
  - `@graphql-codegen/typescript`
  - `@graphql-codegen/typescript-operations`
- Tailwind CSS (already in devDependencies)
- Optional: Switch to Bun's native bundler instead of esbuild

#### Build Strategy (Two Options)

**Option A: Bun Native Bundler (Recommended)**
- Create `assets/build.ts` using `Bun.build()` API
- Native TypeScript support, no transpilation needed
- Faster builds, simpler configuration
- Example:
  ```typescript
  await Bun.build({
    entrypoints: ["js/app.ts"],
    outdir: "../priv/static/assets",
    target: "browser",
    format: "esm",
    minify: !process.argv.includes("--watch"),
    sourcemap: process.argv.includes("--watch") ? "inline" : false,
  });
  ```

**Option B: esbuild via Bun**
- Keep esbuild but run via Bun runtime
- More control over bundling options
- Use if specific esbuild features needed

#### Tailwind Integration

- Update `tailwind.config.js` to scan `.ts` files:
  ```js
  content: [
    "./js/**/*.ts",  // Changed from .js
    "../lib/*_web.ex",
    "../lib/*_web/**/*.*ex"
  ]
  ```
- Works seamlessly with Bun's PostCSS support

### 4. GraphQL Codegen Integration

#### Purpose
- Auto-generate TypeScript types from AshGraphql schema
- End-to-end type safety: Ash Resource → GraphQL Schema → TypeScript
- Updates automatically when Ash resources change

#### Configuration

**codegen.ts** (or codegen.yaml)
```typescript
import { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: 'http://localhost:4000/api/graphql',
  documents: ['js/**/*.ts'],
  generates: {
    './js/generated/types.ts': {
      plugins: ['typescript', 'typescript-operations'],
    },
  },
};

export default config;
```

**Workflow:**
1. Developer changes Ash Resource
2. Phoenix restarts (or schema updates)
3. Run `bun run codegen:watch` (or integrate into dev workflow)
4. TypeScript types update automatically
5. Frontend code gets immediate type safety

### 5. Development Configuration

#### Watcher Setup

**Option A: Using crbelaus/bun Mix Task**
Add to `mix.exs`:
```elixir
defp deps do
  [
    {:bun, "~> 0.1.0", only: :dev}
  ]
end
```

Configure in `config/dev.exs`:
```elixir
config :dnd_app,
  code_reloader: true,
  watchers: [
    bun: {Bun, :install_and_run, [:default, ~w(run watch)]}
  ]
```

**Option B: Manual Watcher**
- Run `bun run watch` separately in terminal
- Document in development guide
- Simpler setup, requires manual process management

#### Live Reload Patterns

Update `config/dev.exs` live_reload patterns to include TypeScript:
```elixir
live_reload: [
  patterns: [
    ~r"priv/static/.*(js|css|png|jpeg|jpg|gif|svg)$",
    ~r"priv/gettext/.*(po)$",
    ~r"lib/dnd_app_web/(controllers|live|components|views)/.*(ex)$",
    ~r"lib/dnd_app_web/templates/.*(eex)$",
    ~r"assets/js/.*(ts)$"  # Add TypeScript files
  ]
]
```

### 6. Build Configuration

#### Config.exs

- Keep esbuild/tailwind configs commented out (handled by Bun)
- Add documentation comments explaining Bun-based build
- Note that assets are compiled via Bun scripts, not Mix tasks

#### Production Build

- `mix assets.deploy` calls `bun run build`
- `mix phx.digest` creates versioned asset files
- Dockerfile builder stage runs `bun install && bun run build`
- Final image excludes node_modules and source files

### 7. Documentation

#### Files to Create

**DOCKER_DEPLOYMENT.md** (Comprehensive Guide)
- Quick Start (Docker Compose)
- Architecture Overview
- Network Configuration
- TypeScript/Bun Setup Instructions
- GraphQL Codegen Setup
- Neo4j Integration (local & Aura cloud)
- Troubleshooting Connection Issues
- Development Workflow
- Production Deployment

#### Files to Update

**CONTAINER_SETUP.md**
- Reference new Docker Compose setup
- Update commands to use Bun
- Link to comprehensive deployment guide

**DEV_SETUP.md**
- Add Bun installation instructions
- Add TypeScript setup steps
- Update asset compilation commands
- Add GraphQL Codegen workflow

**README.md**
- Update quick start with Docker Compose
- Mention TypeScript + Bun stack
- Link to deployment guide

## File Changes Summary

### Files to Create

1. `docker-compose.yml` - Docker Compose configuration
2. `Dockerfile` - Multi-stage Docker build
3. `.dockerignore` - Docker ignore patterns
4. `tsconfig.json` - TypeScript configuration
5. `assets/js/app.ts` - Converted TypeScript entry point
6. `assets/build.ts` - Bun build script (if using native bundler)
7. `codegen.ts` - GraphQL Codegen configuration
8. `DOCKER_DEPLOYMENT.md` - Comprehensive deployment guide

### Files to Modify

1. `assets/js/app.js` → `assets/js/app.ts` - Convert to TypeScript
2. `package.json` - Update scripts for Bun, add GraphQL Codegen
3. `tailwind.config.js` - Update content paths for `.ts` files
4. `config/dev.exs` - Add watcher configuration (optional), update live_reload patterns
5. `config/config.exs` - Document Bun-based build process
6. `mix.exs` - Add Bun mix task dependency (if using Option A watcher)
7. `CONTAINER_SETUP.md` - Update references
8. `DEV_SETUP.md` - Add Bun/TypeScript instructions
9. `README.md` - Update quick start

## Verification Steps

1. ✅ `docker-compose up` starts both services successfully
2. ✅ Phoenix app accessible at `http://localhost:4000`
3. ✅ Neo4j accessible at `http://localhost:7474`
4. ✅ Neo4j connection works from Phoenix container (using service name)
5. ✅ TypeScript compiles without errors (`bun run typecheck`)
6. ✅ Bun builds assets correctly (`bun run build`)
7. ✅ Hot-reload works in development (`bun run watch`)
8. ✅ GraphQL Codegen generates types (`bun run codegen`)
9. ✅ Tailwind CSS compiles correctly
10. ✅ Production build works (`mix assets.deploy`)

## Migration Strategy

### Phase 1: Setup Docker Infrastructure
- Create docker-compose.yml
- Create Dockerfile
- Test basic Docker setup

### Phase 2: TypeScript Migration
- Convert app.js to app.ts
- Create tsconfig.json
- Add type definitions
- Verify compilation

### Phase 3: Bun Integration
- Update package.json
- Set up build scripts
- Test asset compilation
- Update Tailwind config

### Phase 4: GraphQL Codegen
- Install GraphQL Codegen dependencies
- Create codegen configuration
- Test type generation
- Document workflow

### Phase 5: Documentation
- Create comprehensive deployment guide
- Update existing documentation
- Add troubleshooting sections

### Phase 6: Testing & Verification
- Test all verification steps
- Fix any issues
- Final documentation review

## Success Criteria

- Docker Compose setup works out of the box
- TypeScript strict mode enforced (no `any` types in production code)
- Bun builds are fast (< 5 seconds for asset compilation)
- GraphQL types auto-generate and provide type safety
- Development workflow is smooth (hot-reload works)
- Documentation is comprehensive and accurate
- All verification steps pass

## Implementation Todos

### Phase 1: Docker Infrastructure
1. **docker-compose** - Create docker-compose.yml with Neo4j and Phoenix services, health checks, volume mounts, and proper networking
2. **dockerfile** - Create multi-stage Dockerfile with builder stage (Bun + asset compilation) and runtime stage (Alpine + Elixir), removing node_modules after build
3. **dockerignore** - Create .dockerignore to exclude node_modules, _build, deps, and development-only files

### Phase 2: TypeScript Setup
4. **tsconfig** - Create tsconfig.json with strict mode enabled, ES2017+ target, proper module resolution for Phoenix LiveView compatibility
5. **phoenix-types** - Create type definitions for phoenix, phoenix_html, and phoenix_live_view modules (declare modules or find existing types)
6. **convert-to-typescript** - Convert assets/js/app.js to assets/js/app.ts with proper type annotations and module declarations for Phoenix libraries (depends on: tsconfig)

### Phase 3: Bun Integration
7. **package-json-bun** - Update package.json: replace npm scripts with Bun scripts (build, watch, typecheck), ensure Bun compatibility
8. **bun-build-script** - Create assets/build.ts using Bun's native bundler API (Bun.build) for asset compilation, or configure esbuild via Bun (depends on: package-json-bun)
9. **tailwind-config-ts** - Update tailwind.config.js content paths to scan .ts files instead of .js files (depends on: convert-to-typescript)

### Phase 4: Configuration Updates
10. **dev-exs-watcher** - Update config/dev.exs: add Bun watcher configuration (optional, document manual approach as alternative) and update live_reload patterns for .ts files (depends on: package-json-bun)
11. **config-exs-docs** - Update config/config.exs with documentation comments explaining Bun-based build process (keep esbuild/tailwind commented)

### Phase 5: GraphQL Codegen (Future-Ready)
12. **graphql-codegen-setup** - Add GraphQL Codegen dependencies and configuration (codegen.ts) - prepare for future Ash/GraphQL integration (depends on: package-json-bun)

### Phase 6: Documentation
13. **docker-deployment-docs** - Create comprehensive DOCKER_DEPLOYMENT.md with quick start, architecture, network config, TypeScript/Bun setup, Neo4j integration, troubleshooting, and development workflow (depends on: docker-compose, dockerfile)
14. **update-container-setup** - Update CONTAINER_SETUP.md to reference new Docker Compose setup and Bun commands (depends on: docker-deployment-docs)
15. **update-dev-setup** - Update DEV_SETUP.md with Bun installation instructions, TypeScript setup steps, updated asset compilation commands (depends on: docker-deployment-docs)
16. **update-readme** - Update README.md quick start with Docker Compose, mention TypeScript + Bun stack, link to deployment guide (depends on: docker-deployment-docs)

### Phase 7: Verification & Testing
17. **verify-docker** - Test docker-compose up: verify both services start, Phoenix accessible at localhost:4000, Neo4j at localhost:7474, connection works via service name (depends on: docker-compose, dockerfile)
18. **verify-typescript** - Test TypeScript compilation: run bun run typecheck, verify no errors, test strict mode enforcement (depends on: convert-to-typescript, phoenix-types, tsconfig)
19. **verify-bun-build** - Test Bun asset build: run bun run build, verify assets compile correctly, Tailwind CSS works, output in priv/static/assets (depends on: bun-build-script, tailwind-config-ts)
20. **verify-hot-reload** - Test development hot-reload: run bun run watch, verify file changes trigger rebuilds, Phoenix live_reload works (depends on: dev-exs-watcher, bun-build-script)
21. **verify-production-build** - Test production build: run mix assets.deploy, verify digested files created, test production Docker image build (depends on: verify-bun-build, dockerfile)

## Execution Order

The todos are organized by phase with dependencies indicated. Execute in order:
1. Phase 1 (Docker files) - Can be done in parallel
2. Phase 2 (TypeScript setup) - Sequential within phase
3. Phase 3 (Bun integration) - Sequential within phase
4. Phase 4 (Configuration) - Can be done after Phase 3
5. Phase 5 (GraphQL Codegen) - Optional, can be done anytime after Phase 3
6. Phase 6 (Documentation) - Can be written incrementally as work progresses
7. Phase 7 (Verification) - Execute after each relevant phase completes

## Future Enhancements

- Interactive graph visualizations (Cytoscape.js/vis-network) with TypeScript types
- Real-time collaborative RPG tools
- More complex LiveView hooks with full type safety
- GraphQL Codegen integration into CI/CD pipeline (when Ash/GraphQL is added)
- Performance monitoring and optimization

