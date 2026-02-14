defmodule DndApp.RiskRegistry do
  @moduledoc """
  Risk Registry and Dependency Tracking System.

  Tracks technical dependencies, upstream triggers, constraints, and supply chain.
  Provides a centralized system for documenting and querying:
  - Technical dependencies (data sources, packages, services, infrastructure)
  - Risk assessment with severity levels
  - Upstream triggers (events that require updates)
  - Constraints (technical or business limitations)
  - Version tracking for external sources
  - Dependency chains (supply chain / bill of materials)

  ## Usage

      # Register a dependency
      DndApp.RiskRegistry.register_dependency("5etools-data", :data_source, %{
        source_url: "https://github.com/5etools-mirror-1/5etools",
        local_path: "priv/data/5etools"
      })

      # Register a risk
      DndApp.RiskRegistry.register_risk("5etools-data",
        "Upstream repository may change structure",
        :medium,
        %{impact: "Data import pipeline may break"})

      # Track a version
      DndApp.RiskRegistry.track_version("5etools-data", "latest", "abc123")
  """
  require Logger
  alias DndApp.DB.Neo4j

  @dependency_types [:data_source, :package, :service, :infrastructure, :component]
  @severity_levels [:low, :medium, :high, :critical]

  @doc """
  Register a technical dependency.

  ## Parameters
  - `name` - Unique name for the dependency
  - `type` - One of: `:data_source`, `:package`, `:service`, `:infrastructure`, `:component`
  - `metadata` - Map of additional properties (source_url, version, etc.)

  ## Examples

      DndApp.RiskRegistry.register_dependency("neo4j", :service, %{
        version: "5-community",
        connection_url: "bolt://localhost:7687"
      })
  """
  def register_dependency(name, type, metadata \\ %{}) when type in @dependency_types do
    # Build SET clause for metadata properties using parameters
    {set_clauses, param_keys} = build_set_clauses(metadata, "d")

    cypher = """
    MERGE (d:Dependency {name: $name})
    SET d.type = $type,
        d.updated_at = datetime()
        #{if length(set_clauses) > 0, do: ",\n        " <> Enum.join(set_clauses, ",\n        "), else: ""}
    ON CREATE SET d.created_at = datetime()
    RETURN d.name as name
    """

    # Build params map with prefixed keys for metadata
    metadata_params = Enum.into(param_keys, %{}, fn key ->
      {"metadata_#{key}", metadata[key]}
    end)

    params = Map.merge(%{
      name: name,
      type: Atom.to_string(type)
    }, metadata_params)

    case Neo4j.query(cypher, params) do
      {:ok, _} ->
        Logger.info("Registered dependency: #{name} (#{type})")
        :ok
      error ->
        Logger.error("Failed to register dependency #{name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Register a risk associated with a dependency.

  ## Parameters
  - `dependency_name` - Name of the dependency
  - `description` - Description of the risk
  - `severity` - One of: `:low`, `:medium`, `:high`, `:critical`
  - `metadata` - Map with additional info (impact, mitigation, etc.)

  ## Examples

      DndApp.RiskRegistry.register_risk("neo4j",
        "Database connection failure",
        :critical,
        %{impact: "Application cannot function", mitigation: "Connection retry logic"})
  """
  def register_risk(dependency_name, description, severity, metadata \\ %{})
      when severity in @severity_levels do
    risk_id = generate_id()

    {set_clauses, param_keys} = build_set_clauses(metadata, "r")
    metadata_params = Enum.into(param_keys, %{}, fn key ->
      {"metadata_#{key}", metadata[key]}
    end)

    cypher = """
    MATCH (d:Dependency {name: $dependency_name})
    MERGE (r:Risk {id: $risk_id})
    SET r.description = $description,
        r.severity = $severity,
        r.updated_at = datetime()
        #{if length(set_clauses) > 0, do: ",\n        " <> Enum.join(set_clauses, ",\n        "), else: ""}
    ON CREATE SET r.created_at = datetime()

    MERGE (d)-[:HAS_RISK]->(r)
    RETURN r.id as id
    """

    params = Map.merge(%{
      dependency_name: dependency_name,
      risk_id: risk_id,
      description: description,
      severity: Atom.to_string(severity)
    }, metadata_params)

    case Neo4j.query(cypher, params) do
      {:ok, _} ->
        Logger.info("Registered risk for #{dependency_name}: #{description} (#{severity})")
        :ok
      error ->
        Logger.error("Failed to register risk for #{dependency_name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Register an upstream trigger for a dependency.

  Upstream triggers are events that indicate when external data or dependencies
  have changed and may require updates.

  ## Parameters
  - `dependency_name` - Name of the dependency
  - `trigger_type` - Type of trigger (`:git_commit`, `:version_change`, `:file_change`, etc.)
  - `metadata` - Map with trigger configuration (check_command, action, notification, etc.)

  ## Examples

      DndApp.RiskRegistry.register_upstream_trigger("5etools-data", :git_commit, %{
        check_command: "git -C priv/data/5etools rev-parse HEAD",
        action: "run_import",
        notification: true
      })
  """
  def register_upstream_trigger(dependency_name, trigger_type, metadata \\ %{}) do
    trigger_id = generate_id()

    {set_clauses, param_keys} = build_set_clauses(metadata, "t")
    metadata_params = Enum.into(param_keys, %{}, fn key ->
      {"metadata_#{key}", metadata[key]}
    end)

    cypher = """
    MATCH (d:Dependency {name: $dependency_name})
    MERGE (t:Trigger {id: $trigger_id})
    SET t.type = $trigger_type,
        t.updated_at = datetime()
        #{if length(set_clauses) > 0, do: ",\n        " <> Enum.join(set_clauses, ",\n        "), else: ""}
    ON CREATE SET t.created_at = datetime()

    MERGE (d)-[:HAS_TRIGGER]->(t)
    RETURN t.id as id
    """

    params = Map.merge(%{
      dependency_name: dependency_name,
      trigger_id: trigger_id,
      trigger_type: Atom.to_string(trigger_type)
    }, metadata_params)

    case Neo4j.query(cypher, params) do
      {:ok, _} ->
        Logger.info("Registered trigger for #{dependency_name}: #{trigger_type}")
        :ok
      error ->
        Logger.error("Failed to register trigger for #{dependency_name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Register a constraint for a dependency.

  Constraints represent technical or business limitations that affect how
  a dependency is used.

  ## Parameters
  - `dependency_name` - Name of the dependency
  - `constraint_type` - Type of constraint (e.g., `:srd_only`, `:license`, `:version_range`)
  - `description` - Description of the constraint
  - `enforced` - Boolean indicating if the constraint is actively enforced

  ## Examples

      DndApp.RiskRegistry.register_constraint("5etools-data", :srd_only,
        "Only SRD content is imported by default", true)
  """
  def register_constraint(dependency_name, constraint_type, description, enforced \\ true) do
    constraint_id = generate_id()

    cypher = """
    MATCH (d:Dependency {name: $dependency_name})
    MERGE (c:Constraint {id: $constraint_id})
    SET c.type = $constraint_type,
        c.description = $description,
        c.enforced = $enforced,
        c.updated_at = datetime()
    ON CREATE SET c.created_at = datetime()

    MERGE (d)-[:HAS_CONSTRAINT]->(c)
    RETURN c.id as id
    """

    params = %{
      dependency_name: dependency_name,
      constraint_id: constraint_id,
      constraint_type: Atom.to_string(constraint_type),
      description: description,
      enforced: enforced
    }

    case Neo4j.query(cypher, params) do
      {:ok, _} ->
        Logger.info("Registered constraint for #{dependency_name}: #{constraint_type}")
        :ok
      error ->
        Logger.error("Failed to register constraint for #{dependency_name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Track a version/commit of an external dependency.

  This creates a version record that can be used to detect changes
  and trigger updates.

  ## Parameters
  - `dependency_name` - Name of the dependency
  - `version` - Version string or identifier
  - `commit_hash` - Optional git commit hash
  - `metadata` - Additional metadata (timestamp, source, etc.)

  ## Examples

      DndApp.RiskRegistry.track_version("5etools-data", "latest", "abc123def456")
  """
  def track_version(dependency_name, version, commit_hash \\ nil, metadata \\ %{}) do
    version_id = generate_id()

    {set_clauses, param_keys} = build_set_clauses(metadata, "v")
    metadata_params = Enum.into(param_keys, %{}, fn key ->
      {"metadata_#{key}", metadata[key]}
    end)

    cypher = """
    MATCH (d:Dependency {name: $dependency_name})
    MERGE (v:Version {id: $version_id})
    SET v.version = $version,
        v.commit_hash = $commit_hash,
        v.timestamp = datetime(),
        v.updated_at = datetime()
        #{if length(set_clauses) > 0, do: ",\n        " <> Enum.join(set_clauses, ",\n        "), else: ""}
    ON CREATE SET v.created_at = datetime()

    MERGE (d)-[:HAS_VERSION]->(v)
    RETURN v.id as id, v.version as version, v.commit_hash as commit_hash
    """

    params = Map.merge(%{
      dependency_name: dependency_name,
      version_id: version_id,
      version: version,
      commit_hash: commit_hash
    }, metadata_params)

    case Neo4j.query(cypher, params) do
      {:ok, [record | _]} ->
        Logger.info("Tracked version for #{dependency_name}: #{version} (#{commit_hash || "no hash"})")
        {:ok, record}
      error ->
        Logger.error("Failed to track version for #{dependency_name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Get the latest version for a dependency.

  Returns the most recent version record.
  """
  def get_latest_version(dependency_name) do
    cypher = """
    MATCH (d:Dependency {name: $dependency_name})-[:HAS_VERSION]->(v:Version)
    RETURN v.version as version, v.commit_hash as commit_hash, v.timestamp as timestamp
    ORDER BY v.timestamp DESC
    LIMIT 1
    """

    case Neo4j.query(cypher, %{dependency_name: dependency_name}) do
      {:ok, []} -> {:error, :not_found}
      {:ok, [record | _]} -> {:ok, record}
      error -> error
    end
  end

  @doc """
  Create a dependency relationship (supply chain / bill of materials).

  Indicates that one dependency depends on another.

  ## Examples

      DndApp.RiskRegistry.add_dependency_relationship("dnd-app", "neo4j")
      DndApp.RiskRegistry.add_dependency_relationship("dnd-app", "5etools-data")
  """
  def add_dependency_relationship(dependent_name, dependency_name, metadata \\ %{}) do
    {set_clauses, param_keys} = build_set_clauses(metadata, "rel")
    metadata_params = Enum.into(param_keys, %{}, fn key ->
      {"metadata_#{key}", metadata[key]}
    end)

    cypher = """
    MATCH (dependent:Dependency {name: $dependent_name})
    MATCH (dependency:Dependency {name: $dependency_name})
    MERGE (dependent)-[rel:DEPENDS_ON]->(dependency)
    SET rel.updated_at = datetime()
        #{if length(set_clauses) > 0, do: ",\n        " <> Enum.join(set_clauses, ",\n        "), else: ""}
    ON CREATE SET rel.created_at = datetime()
    RETURN dependent.name as dependent, dependency.name as dependency
    """

    params = Map.merge(%{
      dependent_name: dependent_name,
      dependency_name: dependency_name
    }, metadata_params)

    case Neo4j.query(cypher, params) do
      {:ok, _} ->
        Logger.info("Created dependency relationship: #{dependent_name} -> #{dependency_name}")
        :ok
      error ->
        Logger.error("Failed to create dependency relationship: #{inspect(error)}")
        error
    end
  end

  @doc """
  Link a dependency to a component that uses it.

  ## Examples

      DndApp.RiskRegistry.link_to_component("5etools-data", "data-import-pipeline")
  """
  def link_to_component(dependency_name, component_name, component_type \\ :pipeline) do
    cypher = """
    MATCH (d:Dependency {name: $dependency_name})
    MERGE (c:Component {name: $component_name})
    SET c.type = $component_type,
        c.updated_at = datetime()
    ON CREATE SET c.created_at = datetime()

    MERGE (c)-[:USES]->(d)
    RETURN c.name as component, d.name as dependency
    """

    params = %{
      dependency_name: dependency_name,
      component_name: component_name,
      component_type: Atom.to_string(component_type)
    }

    case Neo4j.query(cypher, params) do
      {:ok, _} ->
        Logger.info("Linked #{dependency_name} to component #{component_name}")
        :ok
      error ->
        Logger.error("Failed to link dependency to component: #{inspect(error)}")
        error
    end
  end

  @doc """
  Query all critical risks.

  Returns all risks with severity :critical.
  """
  def get_critical_risks do
    cypher = """
    MATCH (d:Dependency)-[:HAS_RISK]->(r:Risk)
    WHERE r.severity = 'critical'
    RETURN d.name as dependency, r.description as description, r.impact as impact, r.mitigation as mitigation
    ORDER BY d.name
    """

    case Neo4j.query(cypher) do
      {:ok, records} -> {:ok, records}
      error -> error
    end
  end

  @doc """
  Get the dependency chain (supply chain / bill of materials) for a dependency.

  Returns all dependencies in the chain, including transitive dependencies.
  """
  def get_dependency_chain(dependency_name) do
    cypher = """
    MATCH path = (d:Dependency {name: $dependency_name})-[:DEPENDS_ON*]->(parent:Dependency)
    RETURN path
    ORDER BY length(path) DESC
    """

    case Neo4j.query(cypher, %{dependency_name: dependency_name}) do
      {:ok, records} -> {:ok, records}
      error -> error
    end
  end

  @doc """
  Get all upstream triggers for a dependency.
  """
  def get_upstream_triggers(dependency_name) do
    cypher = """
    MATCH (d:Dependency {name: $dependency_name})-[:HAS_TRIGGER]->(t:Trigger)
    RETURN t.type as type, t.check_command as check_command, t.action as action, t.notification as notification
    """

    case Neo4j.query(cypher, %{dependency_name: dependency_name}) do
      {:ok, records} -> {:ok, records}
      error -> error
    end
  end

  @doc """
  Get all constraints for a dependency.
  """
  def get_constraints(dependency_name) do
    cypher = """
    MATCH (d:Dependency {name: $dependency_name})-[:HAS_CONSTRAINT]->(c:Constraint)
    RETURN c.type as type, c.description as description, c.enforced as enforced
    """

    case Neo4j.query(cypher, %{dependency_name: dependency_name}) do
      {:ok, records} -> {:ok, records}
      error -> error
    end
  end

  @doc """
  Get version history for a dependency.
  """
  def get_version_history(dependency_name, limit \\ 10) do
    cypher = """
    MATCH (d:Dependency {name: $dependency_name})-[:HAS_VERSION]->(v:Version)
    RETURN v.version as version, v.commit_hash as commit_hash, v.timestamp as timestamp
    ORDER BY v.timestamp DESC
    LIMIT $limit
    """

    case Neo4j.query(cypher, %{dependency_name: dependency_name, limit: limit}) do
      {:ok, records} -> {:ok, records}
      error -> error
    end
  end

  # Generate a unique ID for nodes
  defp generate_id do
    UUID.uuid4()
  end

  # Build SET clauses for dynamic properties using parameters
  defp build_set_clauses(metadata, prefix) when is_map(metadata) do
    clauses = metadata
    |> Enum.map(fn {key, _value} ->
      param_name = "metadata_#{key}"
      "#{prefix}.#{key} = $#{param_name}"
    end)

    param_keys = Map.keys(metadata)
    {clauses, param_keys}
  end

  defp build_set_clauses(_, _), do: {[], []}
end
