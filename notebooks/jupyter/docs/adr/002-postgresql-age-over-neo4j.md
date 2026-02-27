# ADR-002: PostgreSQL + Apache AGE replaces Neo4j

## Status

Accepted

## Context

The system used Neo4j for graph data (creator relationships, content graphs). Running
Neo4j as a separate service adds operational cost and a second query language surface.
The existing PostgreSQL instance already handles relational and vector data (pgvector).

Apache AGE is a PostgreSQL extension that adds a Cypher-compatible graph query layer
directly inside Postgres. It exposes the same `MATCH/CREATE/RETURN` Cypher syntax used
by Neo4j.

## Decision

Use PostgreSQL with Apache AGE for all graph data. The `AGEAdapter` in `infra/psql/age.py`
provides a Neo4j-like interface over Postgres so call sites change minimally.

The pgvector image (`pgvector/pgvector:pg16`) is used as the base since it already ships
Postgres 16 with the vector extension; AGE is installed on top.

## Consequences

- Neo4j service removed. Single database service handles relational, vector, and graph data.
- Single backup/restore target, single connection pool.
- AGE's `cypher()` SQL wrapper requires the return column signature to exactly match the
  Cypher RETURN clause — this is the primary source of bugs and is addressed in ADR-004.
- AGE does not support all Neo4j Cypher features (e.g. some path functions). Queries must
  be validated against the AGE documentation.
