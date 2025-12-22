# Risk Registry and Dependency Tracking

## Overview

The Risk Registry is a comprehensive system for tracking technical dependencies, risks, constraints, and upstream triggers for the Kino project. It uses Neo4j to maintain a knowledge graph of all dependencies and their relationships, enabling:

- **Dependency Tracking**: Document all technical dependencies (data sources, packages, services, infrastructure)
- **Risk Assessment**: Identify and track risks with severity levels
- **Upstream Triggers**: Monitor external data sources for changes
- **Constraint Documentation**: Track technical and business constraints
- **Supply Chain Visibility**: Understand dependency chains (bill of materials)
- **Version Tracking**: Monitor versions and changes in external dependencies

## Architecture

The Risk Registry is implemented as a Neo4j knowledge graph with the following structure:

```
(Dependency {name, type, metadata})
  -[:HAS_RISK]->(Risk {description, severity, impact, mitigation})
  -[:HAS_TRIGGER]->(Trigger {type, check_command, action})
  -[:HAS_CONSTRAINT]->(Constraint {type, description, enforced})
  -[:HAS_VERSION]->(Version {version, commit_hash, timestamp})
  -[:DEPENDS_ON]->(Dependency)  // Dependency chain
  -[:AFFECTS]->(Component {name, type})  // Components using this dependency
```

### Node Types

#### Dependency
Represents any technical dependency:
- **Types**: `data_source`, `package`, `service`, `infrastructure`, `component`
- **Properties**: `name`, `type`, `source_url`, `version`, `metadata`

#### Risk
Identified risks associated with dependencies:
- **Severity Levels**: `low`, `medium`, `high`, `critical`
- **Properties**: `description`, `severity`, `impact`, `mitigation`

#### Trigger
Upstream triggers that indicate when external dependencies change:
- **Types**: `git_commit`, `version_change`, `file_change`
- **Properties**: `type`, `check_command`, `action`, `notification`

#### Constraint
Technical or business constraints:
- **Types**: `srd_only`, `license`, `version_range`, `manual_update`
- **Properties**: `type`, `description`, `enforced`

#### Version
Version tracking for external dependencies:
- **Properties**: `version`, `commit_hash`, `timestamp`

#### Component
Application components that use dependencies:
- **Types**: `application`, `pipeline`, `service`
- **Properties**: `name`, `type`

## Usage

### Initial Setup

1. **Register Dependencies**: Run the registration task to populate the registry:

```bash
mix register.dependencies
```

This will:
- Register all data source dependencies (5etools, etc.)
- Register all package dependencies from `mix.exs`
- Register service dependencies (Neo4j, etc.)
- Register infrastructure dependencies (Docker, Elixir, etc.)
- Create dependency relationships
- Link dependencies to components

2. **Verify in Neo4j Browser**: Open http://localhost:7474 and run:

```cypher
MATCH (d:Dependency)
RETURN d.name, d.type
ORDER BY d.type, d.name
```

### Manual Registration

You can also register dependencies programmatically:

```elixir
# Register a dependency
DndApp.RiskRegistry.register_dependency(
  "my-data-source",
  :data_source,
  %{
    source_url: "https://example.com/data",
    local_path: "priv/data/mysource"
  }
)

# Register a risk
DndApp.RiskRegistry.register_risk(
  "my-data-source",
  "API may change without notice",
  :medium,
  %{
    impact: "Data import may break",
    mitigation: "Monitor API changes, maintain version pinning"
  }
)

# Register an upstream trigger
DndApp.RiskRegistry.register_upstream_trigger(
  "my-data-source",
  :version_change,
  %{
    check_command: "curl -s https://api.example.com/version",
    action: "run_import",
    notification: true
  }
)

# Track a version
DndApp.RiskRegistry.track_version(
  "my-data-source",
  "v1.2.3",
  "abc123def456"
)
```

### Version Tracking

The import task automatically tracks versions after successful imports:

```bash
mix import.5etools
```

This will:
- Get the current git commit hash (if available)
- Track the version in the registry
- Compare with previous versions
- Alert if version changed

## Querying the Risk Registry

### Get All Dependencies

```cypher
MATCH (d:Dependency)
RETURN d.name, d.type, d.source_url
ORDER BY d.type, d.name
```

### Get Critical Risks

```cypher
MATCH (d:Dependency)-[:HAS_RISK]->(r:Risk)
WHERE r.severity = 'critical'
RETURN d.name as dependency, 
       r.description as description, 
       r.impact as impact,
       r.mitigation as mitigation
ORDER BY d.name
```

Or use the Elixir function:

```elixir
{:ok, risks} = DndApp.RiskRegistry.get_critical_risks()
```

### Get Dependency Chain (Supply Chain)

```cypher
MATCH path = (d:Dependency {name: 'dnd-app'})-[:DEPENDS_ON*]->(parent:Dependency)
RETURN path
ORDER BY length(path) DESC
```

Or use the Elixir function:

```elixir
{:ok, chain} = DndApp.RiskRegistry.get_dependency_chain("dnd-app")
```

### Get Upstream Triggers

```cypher
MATCH (d:Dependency {name: '5etools-data'})-[:HAS_TRIGGER]->(t:Trigger)
RETURN d.name, t.type, t.check_command, t.action, t.notification
```

Or use the Elixir function:

```elixir
{:ok, triggers} = DndApp.RiskRegistry.get_upstream_triggers("5etools-data")
```

### Get Constraints

```cypher
MATCH (d:Dependency {name: '5etools-data'})-[:HAS_CONSTRAINT]->(c:Constraint)
WHERE c.enforced = true
RETURN d.name, c.type, c.description
```

Or use the Elixir function:

```elixir
{:ok, constraints} = DndApp.RiskRegistry.get_constraints("5etools-data")
```

### Get Version History

```cypher
MATCH (d:Dependency {name: '5etools-data'})-[:HAS_VERSION]->(v:Version)
RETURN v.version, v.commit_hash, v.timestamp
ORDER BY v.timestamp DESC
LIMIT 10
```

Or use the Elixir function:

```elixir
{:ok, versions} = DndApp.RiskRegistry.get_version_history("5etools-data", 10)
```

### Get Components Using a Dependency

```cypher
MATCH (c:Component)-[:USES]->(d:Dependency {name: 'neo4j'})
RETURN c.name, c.type
```

### Get All Risks by Severity

```cypher
MATCH (d:Dependency)-[:HAS_RISK]->(r:Risk)
RETURN r.severity, count(*) as count
ORDER BY 
  CASE r.severity
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
  END
```

### Find Dependencies with No Risk Assessment

```cypher
MATCH (d:Dependency)
WHERE NOT (d)-[:HAS_RISK]->()
RETURN d.name, d.type
ORDER BY d.type, d.name
```

### Get Dependency Impact Analysis

```cypher
MATCH (d:Dependency {name: 'neo4j'})<-[:DEPENDS_ON*]-(dependent:Dependency)
RETURN dependent.name, dependent.type, length(path) as depth
ORDER BY depth
```

## Common Workflows

### Adding a New Dependency

1. Register the dependency:
```elixir
DndApp.RiskRegistry.register_dependency("new-service", :service, %{...})
```

2. Assess and register risks:
```elixir
DndApp.RiskRegistry.register_risk("new-service", "Description", :high, %{...})
```

3. Register constraints if any:
```elixir
DndApp.RiskRegistry.register_constraint("new-service", :license, "MIT License", true)
```

4. Create dependency relationships:
```elixir
DndApp.RiskRegistry.add_dependency_relationship("dnd-app", "new-service")
```

5. Link to components:
```elixir
DndApp.RiskRegistry.link_to_component("new-service", "dnd-app", :application)
```

### Monitoring Upstream Changes

1. Register an upstream trigger:
```elixir
DndApp.RiskRegistry.register_upstream_trigger(
  "5etools-data",
  :git_commit,
  %{
    check_command: "git -C priv/data/5etools rev-parse HEAD",
    action: "run_import",
    notification: true
  }
)
```

2. Check for changes before import:
```elixir
{:ok, current_version} = DndApp.RiskRegistry.get_latest_version("5etools-data")
# Compare with current git hash
```

3. Track version after import:
```elixir
DndApp.RiskRegistry.track_version("5etools-data", "latest", commit_hash)
```

### Risk Assessment Workflow

1. Query all dependencies without risk assessment:
```cypher
MATCH (d:Dependency)
WHERE NOT (d)-[:HAS_RISK]->()
RETURN d.name, d.type
```

2. For each dependency, assess risks:
   - Identify potential failure modes
   - Determine severity (low, medium, high, critical)
   - Document impact and mitigation strategies

3. Register risks:
```elixir
DndApp.RiskRegistry.register_risk(dependency_name, description, severity, %{
  impact: "...",
  mitigation: "..."
})
```

4. Review critical risks regularly:
```elixir
{:ok, critical_risks} = DndApp.RiskRegistry.get_critical_risks()
```

## Integration with Data Import

The import task (`mix import.5etools`) automatically tracks versions after successful imports. This enables:

- **Change Detection**: Compare current version with previous versions
- **Audit Trail**: Track when data was imported and from which version
- **Rollback Capability**: Identify which version was used for a specific import

### Example Output

```
========================================
5etools Data Import
========================================
Path: priv/data/5etools
SRD Only: false
========================================

✅ Import completed successfully!

📊 Tracking import version...
  ✓ Version tracked: latest
  ✓ Commit hash: abc12345...
  ℹ️  No version change detected
```

## Best Practices

1. **Regular Updates**: Run `mix register.dependencies` after adding new dependencies
2. **Risk Assessment**: Assess risks for all critical dependencies
3. **Version Tracking**: Track versions for all external data sources
4. **Constraint Documentation**: Document all constraints that affect usage
5. **Dependency Relationships**: Maintain accurate dependency chains
6. **Regular Reviews**: Review critical risks periodically
7. **Change Monitoring**: Set up upstream triggers for critical data sources

## Troubleshooting

### Dependencies Not Appearing

If dependencies don't appear after registration:

1. Check Neo4j connection:
```bash
# In Neo4j Browser
MATCH (d:Dependency) RETURN count(d)
```

2. Verify schema was created:
```cypher
SHOW CONSTRAINTS
```

3. Check for errors in logs:
```bash
# Look for registration errors
tail -f log/dev.log | grep RiskRegistry
```

### APOC Functions Not Available

Some functions use APOC (Awesome Procedures on Cypher). Ensure APOC is installed:

```bash
# In docker-compose.yml
environment:
  - NEO4J_PLUGINS=["apoc"]
```

### Version Tracking Not Working

If version tracking fails:

1. Check if git is available:
```bash
git --version
```

2. Verify path is correct:
```bash
ls -la priv/data/5etools
```

3. Check if it's a git repository or submodule:
```bash
git -C priv/data/5etools rev-parse HEAD
```

## Related Documentation

- [Architecture Documentation](ARCHITECTURE.md) - Overall system architecture
- [Data Import Guide](DATA_IMPORT.md) - How to import game data
- [Neo4j Setup Guide](START_WITH_EXISTING_NEO4J.md) - Neo4j configuration
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

## API Reference

See `lib/dnd_app/risk_registry.ex` for complete API documentation.

### Main Functions

- `register_dependency/3` - Register a technical dependency
- `register_risk/4` - Register a risk for a dependency
- `register_upstream_trigger/3` - Register an upstream trigger
- `register_constraint/4` - Register a constraint
- `track_version/4` - Track a version/commit
- `get_latest_version/1` - Get the latest version
- `get_critical_risks/0` - Get all critical risks
- `get_dependency_chain/1` - Get dependency chain
- `get_upstream_triggers/1` - Get upstream triggers
- `get_constraints/1` - Get constraints
- `get_version_history/2` - Get version history

