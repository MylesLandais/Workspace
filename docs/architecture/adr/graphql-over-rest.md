# GraphQL over REST

## Status

Accepted

## Context

We need an API layer between the Astro frontend and Phoenix/Ash backend. The frontend needs flexible querying capabilities for the feed view, subscription management, and real-time updates.

## Decision

Use GraphQL (via Ash GraphQL / Absinthe) instead of REST for the API layer.

## Rationale

**Flexible Queries**: The feed view needs different data shapes depending on context (infinite scroll vs detail view). GraphQL allows clients to request exactly the fields needed.

**Real-time Subscriptions**: GraphQL subscriptions (via Phoenix Channels) provide a clean way to push pipeline status updates to the frontend without polling.

**Type Safety**: GraphQL schema enables code generation for TypeScript types and React hooks, reducing runtime errors.

**Single Endpoint**: Simpler client configuration and authentication compared to multiple REST endpoints.

## Consequences

**Positive**:
- Frontend can optimize queries per view
- Strong typing with code generation
- Built-in introspection for tooling
- Subscriptions for real-time features

**Negative**:
- More complex backend setup (Ash GraphQL integration)
- Query complexity analysis needed to prevent abuse
- Caching more complex than REST (though Apollo Client handles this)

**Neutral**:
- Learning curve for team members new to GraphQL
- Tooling ecosystem is mature and well-supported

## Alternatives Considered

**REST**: Simpler to implement but less flexible. Would require multiple endpoints or over-fetching.

**tRPC**: Type-safe but requires TypeScript on backend. We're using Elixir/Phoenix.

## References

- Ash GraphQL documentation
- Apollo Client best practices






