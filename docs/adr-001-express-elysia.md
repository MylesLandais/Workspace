# Architecture Decision: Express + Apollo Server vs Elysia.js

## Context

CLAUDE.md originally documented Elysia.js (Bun-native) + Eden as the server tech stack, but the actual implementation uses Express.js + Apollo Server.

## Decision

**Keep Express.js + Apollo Server**

## Rationale

### Advantages of Current Stack (Express + Apollo)

1. **Maturity & Stability**
   - Express has been battle-tested since 2010
   - Apollo Server is the de facto standard for GraphQL in Node.js
   - Extensive documentation and community resources
   - Well-understood patterns and best practices

2. **Development Ecosystem**
   - Large library ecosystem (middleware, tools, utilities)
   - Abundant examples and tutorials
   - Easy to find developers with experience
   - Strong tooling support (debugging, profiling)

3. **GraphQL Ecosystem**
   - Apollo Server provides first-class GraphQL features:
     - Built-in query complexity analysis
     - Response caching plugin
     - Subscriptions via WebSocket
     - Tracing and monitoring integrations
   - Apollo Client has excellent frontend integration
   - Code generation tools (GraphQL Code Generator)

4. **Current Investment**
   - Server is already implemented with Express + Apollo
   - Neo4j integration uses Apollo's resolvers pattern
   - Type definitions already structured for GraphQL
   - Migration cost would be high with unclear benefits

5. **Performance Considerations**
   - Express is fast enough for current workload
   - GraphQL execution time (Neo4j queries) dwarfs HTTP overhead
   - Valkey caching provides sub-millisecond response times
   - No identified performance bottleneck in HTTP layer

### Disadvantages of Elysia.js Migration

1. **Immaturity**
   - Elysia.js is relatively new (2022)
   - Smaller community and ecosystem
   - Less battle-tested in production
   - Fewer examples and documentation

2. **GraphQL Support**
   - Elysia's GraphQL support is less mature
   - Would require significant refactoring
   - No built-in Apollo-equivalent features
   - Would need to implement many features from scratch

3. **Developer Experience**
   - Less familiar to most Node.js developers
   - Steeper learning curve for new team members
   - Fewer debugging and monitoring tools

4. **Bun Compatibility**
   - Express works perfectly fine with Node.js
   - Current architecture separates client (Bun) and server (Node.js)
   - No requirement for server to run on Bun
   - Docker handles runtime consistency

## When to Reconsider

Consider migration to Elysia.js if:

1. **Performance Bottleneck Identified**
   - HTTP layer becomes the primary bottleneck
   - Benchmarking shows 2x+ improvement with Elysia
   - Current Express implementation can't meet SLA

2. **Elysia Ecosystem Matures**
   - GraphQL support reaches parity with Apollo
   - Major production deployments demonstrate stability
   - Developer experience improves significantly

3. **Business Requirements Change**
   - Requirement for server to run on Bun becomes critical
   - Need to reduce dependencies (though Apollo is valuable)
   - Team expertise shifts to Elysia ecosystem

## Alternatives Considered

### 1. Keep Express, Use Elysia for New Services
**Status**: Not recommended
**Rationale**: Mixed stack complexity outweighs benefits

### 2. Use Fastify instead of Express
**Status**: Considered but rejected
**Rationale**: Express performance is sufficient, migration cost not justified

### 3. Pure GraphQL with Yoga
**Status**: Considered but rejected
**Rationale**: Apollo Server has more features and better tooling

## Related Decisions

- [Shared Types Architecture](./shared-types.md) - For client-server type safety
- [Caching Strategy](./caching.md) - Valkey for hot data paths
- [Graph Database](./neo4j.md) - Neo4j for relationship queries

## References

- Apollo Server: https://www.apollographql.com/docs/apollo-server/
- Express.js: https://expressjs.com/
- Elysia.js: https://elysiajs.com/
- Bun: https://bun.sh/

## Decision Date

January 2, 2026
