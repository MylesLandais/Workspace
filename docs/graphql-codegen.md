# GraphQL Code Generation

This setup uses GraphQL Code Generator to automatically generate TypeScript types from the GraphQL schema, ensuring end-to-end type safety between client and server.

## Setup

### Dependencies

Add these packages to `app/client`:

```bash
cd app/client
bun add -D @graphql-codegen/cli @graphql-codegen/typescript @graphql-codegen/typescript-operations @graphql-codegen/typescript-react-apollo @graphql-tools/extract graphql-tag
```

### Configuration

- **Config**: `codegen.yml` at project root
- **Schema Loader**: `schema-loader.js` for extracting Apollo schema
- **Output**: `app/client/src/lib/generated/graphql.ts`

## Usage

### Generate Types

```bash
# One-time generation
bun run codegen

# Watch mode for development
bun run codegen:watch
```

## Generated Types

The generator creates:

1. **GraphQL Types** - All schema types (Query, Mutation, Types, Inputs)
2. **Operation Types** - Typed queries and mutations
3. **React Hooks** - `useQuery`, `useMutation` hooks with proper types

### Example Usage

```typescript
import { useQuery } from "@apollo/client";
import { GetFeedDocument, GetFeedQuery } from "../lib/generated/graphql";

// Hook with full type safety
const { data, loading, error } = useQuery(GetFeedDocument);

// data is typed as GetFeedQuery | undefined
const items = data?.feed?.edges ?? [];
```

## Benefits

1. **Type Safety** - Catch errors at compile time, not runtime
2. **Autocomplete** - IDE suggestions for all fields
3. **Refactoring** - Safe schema changes with compile-time errors
4. **Documentation** - Types serve as API documentation
5. **Consistency** - Single source of truth from GraphQL schema

## Schema Changes

When modifying GraphQL schema:

1. Update `app/server/src/schema/schema.ts`
2. Run `bun run codegen`
3. Fix any TypeScript errors in client code
4. Update operations that use changed fields

## Migration Path

### Current State

- Client uses manual type definitions (`src/lib/types/`)
- No generated types from GraphQL schema
- Risk of schema/client mismatch

### Target State

- All GraphQL operations use generated types
- Manual types only for non-GraphQL data (mock, UI state)
- Full end-to-end type safety

### Steps to Migrate

1. [DONE] Set up codegen configuration
2. Run initial generation: `bun run codegen`
3. Convert one operation at a time:

   ```typescript
   // Before
   interface FeedItem { ... }

   // After
   const { data } = useQuery(GET_FEED);
   type FeedItem = GetFeedQuery['feed']['edges'][0]['node'];
   ```

4. Remove manual types as they become unused
5. Add codegen to CI pipeline

## Troubleshooting

### Schema Not Found

- Ensure server is running at `http://localhost:4002`
- Check `codegen.yml` schema path

### Type Conflicts

- Remove manual type definitions
- Use generated types exclusively for GraphQL data

### Missing Imports

- Import from `lib/generated/graphql`
- Not from manual type files

## References

- GraphQL Code Generator: https://the-guild.dev/graphql/codegen
- Apollo TypeScript Docs: https://www.apollographql.com/docs/react/development-testing/static-typing/
