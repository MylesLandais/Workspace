# ADR-004: AGE adapter must infer or accept explicit return columns

## Status

Accepted

## Context

AGE's `cypher()` SQL wrapper requires the column list in `AS (col agtype)` to exactly
match the number and names of columns in the Cypher RETURN clause. The original
implementation hardcoded `v agtype` or `count agtype` based on a string heuristic,
causing silent failures for multi-column returns and named aliases.

Additionally, AGE returns `agtype` values as PostgreSQL custom type strings such as
`{"id": 1, "name": "test"}::vertex`. psycopg2 surfaces these as plain Python strings,
so callers received raw strings rather than dicts.

## Decision

1. `execute_query` accepts an optional `return_columns: list[tuple[str, str]]` parameter.
   When provided, it is used verbatim. When absent, the RETURN clause is parsed with a
   regex to extract column names automatically.

2. All agtype values are post-processed by `_parse_agtype()`, which strips the `::word`
   suffix and JSON-parses the result into a Python dict or scalar.

3. A new `execute_cypher()` convenience method is the recommended entry point for new
   code. It always auto-infers columns and always returns plain dicts.

4. `execute_write` wraps mutations in an explicit `BEGIN`/`COMMIT` since AGE mutations
   require a transaction to be visible.

## Consequences

- Existing call sites using `execute_query` with single-column returns continue to work
  (auto-inference defaults to the first token after RETURN).
- Multi-column returns (`RETURN c, h`) now work correctly.
- Callers receive `[{"uuid": ..., "name": ...}]` instead of raw agtype strings.
- The regex parser is a best-effort heuristic; complex RETURN clauses (subqueries,
  function calls with commas) should pass `return_columns` explicitly.
