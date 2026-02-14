# Risk Registry Quick Reference

## Quick Start

```bash
# Register all dependencies
mix register.dependencies

# View in Neo4j Browser
# Open http://localhost:7474
```

## Common Queries

### View All Dependencies
```cypher
MATCH (d:Dependency)
RETURN d.name, d.type
ORDER BY d.type, d.name
```

### Find Critical Risks
```cypher
MATCH (d:Dependency)-[:HAS_RISK]->(r:Risk)
WHERE r.severity = 'critical'
RETURN d.name, r.description, r.impact
```

### Check Dependency Chain
```cypher
MATCH path = (d:Dependency {name: 'dnd-app'})-[:DEPENDS_ON*]->(parent:Dependency)
RETURN path
```

### Get Version History
```cypher
MATCH (d:Dependency {name: '5etools-data'})-[:HAS_VERSION]->(v:Version)
RETURN v.version, v.commit_hash, v.timestamp
ORDER BY v.timestamp DESC
LIMIT 5
```

## Elixir API

### Register Dependency
```elixir
DndApp.RiskRegistry.register_dependency("name", :type, %{metadata})
```

### Register Risk
```elixir
DndApp.RiskRegistry.register_risk("dependency", "description", :severity, %{impact: "..."})
```

### Track Version
```elixir
DndApp.RiskRegistry.track_version("dependency", "version", "commit_hash")
```

### Get Critical Risks
```elixir
{:ok, risks} = DndApp.RiskRegistry.get_critical_risks()
```

## Dependency Types
- `:data_source` - External data sources (5etools, etc.)
- `:package` - Code dependencies (Phoenix, Boltx, etc.)
- `:service` - External services (Neo4j, APIs, etc.)
- `:infrastructure` - Infrastructure (Docker, Elixir, etc.)
- `:component` - Application components

## Risk Severity Levels
- `:low` - Minor impact, easy to mitigate
- `:medium` - Moderate impact, requires attention
- `:high` - Significant impact, needs mitigation plan
- `:critical` - System-breaking, immediate action required

## See Also
- [Full Documentation](RISK_REGISTRY.md)
- [Architecture Guide](ARCHITECTURE.md)

