defmodule Mix.Tasks.Register.Dependencies do
  @moduledoc """
  Register all technical dependencies in the risk registry.

  This task scans the project and registers:
  - Data source dependencies (5etools, etc.)
  - Package dependencies (from mix.exs)
  - Service dependencies (Neo4j, etc.)
  - Infrastructure dependencies (Docker, etc.)

  Usage: mix register.dependencies
  """
  use Mix.Task

  @shortdoc "Register all technical dependencies in the risk registry"

  def run(_args) do
    Mix.Task.run("app.start")

    IO.puts("""
    ========================================
    Dependency Registration
    ========================================
    Registering all technical dependencies...
    ========================================
    """)

    # Register data source dependencies
    register_data_sources()

    # Register package dependencies
    register_packages()

    # Register service dependencies
    register_services()

    # Register infrastructure dependencies
    register_infrastructure()

    # Create dependency relationships
    create_dependency_relationships()

    IO.puts("\n✅ Dependency registration completed!")
    IO.puts("\nView the risk registry in Neo4j Browser: http://localhost:7474")
    IO.puts("Query example: MATCH (d:Dependency) RETURN d")
  end

  defp register_data_sources do
    IO.puts("\n📦 Registering data source dependencies...")

    # Register 5etools data source
    DndApp.RiskRegistry.register_dependency(
      "5etools-data",
      :data_source,
      %{
        source_url: "https://github.com/5etools-mirror-1/5etools",
        local_path: "priv/data/5etools",
        format: "JSON",
        update_frequency: "manual",
        license: "Community-maintained",
        description: "D&D 5e game data in JSON format"
      }
    )

    # Register risks for 5etools
    DndApp.RiskRegistry.register_risk(
      "5etools-data",
      "Upstream repository may change structure or remove data",
      :medium,
      %{
        impact: "Data import pipeline may break",
        mitigation: "Monitor repository changes, maintain local backups"
      }
    )

    DndApp.RiskRegistry.register_risk(
      "5etools-data",
      "No formal versioning or release process",
      :low,
      %{
        impact: "Difficult to track changes and rollback if needed",
        mitigation: "Track git commit hashes for version control"
      }
    )

    DndApp.RiskRegistry.register_risk(
      "5etools-data",
      "Data format may change without notice",
      :medium,
      %{
        impact: "Import parser may fail on new data structure",
        mitigation: "Validate JSON structure before import, handle errors gracefully"
      }
    )

    # Register upstream trigger
    DndApp.RiskRegistry.register_upstream_trigger(
      "5etools-data",
      :git_commit,
      %{
        check_command: "git -C priv/data/5etools rev-parse HEAD 2>/dev/null || echo 'not-a-git-repo'",
        action: "run_import",
        notification: true,
        description: "Detect changes in git commit hash to trigger data import"
      }
    )

    # Register constraints
    DndApp.RiskRegistry.register_constraint(
      "5etools-data",
      :srd_only,
      "Only SRD (Systems Reference Document) content is imported by default",
      true
    )

    DndApp.RiskRegistry.register_constraint(
      "5etools-data",
      :manual_update,
      "Data updates require manual intervention (no automatic sync)",
      true
    )

    # Link to component
    DndApp.RiskRegistry.link_to_component("5etools-data", "data-import-pipeline", :pipeline)

    IO.puts("  ✓ Registered 5etools-data")
  end

  defp register_packages do
    IO.puts("\n📚 Registering package dependencies...")

    # Read dependencies from mix.exs
    deps = get_mix_dependencies()

    Enum.each(deps, fn {name, version, opts} ->
      source = Keyword.get(opts, :source, "hex.pm")
      type = if Keyword.get(opts, :only) == :test, do: "test", else: "runtime"

      DndApp.RiskRegistry.register_dependency(
        to_string(name),
        :package,
        %{
          version: version,
          source: source,
          type: type,
          package_manager: "mix"
        }
      )

      # Register risks for critical packages
      if name in [:phoenix, :boltx, :jason] do
        DndApp.RiskRegistry.register_risk(
          to_string(name),
          "Breaking changes in major version updates",
          :medium,
          %{
            impact: "May require code changes to maintain compatibility",
            mitigation: "Pin versions, test upgrades in staging"
          }
        )
      end
    end)

    IO.puts("  ✓ Registered #{length(deps)} package dependencies")
  end

  defp register_services do
    IO.puts("\n🔧 Registering service dependencies...")

    # Neo4j
    DndApp.RiskRegistry.register_dependency(
      "neo4j",
      :service,
      %{
        version: "5-community",
        connection_url: "bolt://localhost:7687",
        health_check: "http://localhost:7474",
        critical: true,
        description: "Graph database for storing character and game data"
      }
    )

    DndApp.RiskRegistry.register_risk(
      "neo4j",
      "Database connection failure",
      :critical,
      %{
        impact: "Application cannot function without database",
        mitigation: "Connection retry logic with transient restart policy, health checks"
      }
    )

    DndApp.RiskRegistry.register_risk(
      "neo4j",
      "Database version incompatibility",
      :high,
      %{
        impact: "Driver may not support newer Neo4j features",
        mitigation: "Pin Neo4j version, test driver compatibility"
      }
    )

    DndApp.RiskRegistry.register_constraint(
      "neo4j",
      :version_range,
      "Requires Neo4j 5.x community edition",
      true
    )

    # Link to components
    DndApp.RiskRegistry.link_to_component("neo4j", "dnd-app", :application)
    DndApp.RiskRegistry.link_to_component("neo4j", "data-import-pipeline", :pipeline)

    IO.puts("  ✓ Registered neo4j service")
  end

  defp register_infrastructure do
    IO.puts("\n🏗️  Registering infrastructure dependencies...")

    # Docker
    DndApp.RiskRegistry.register_dependency(
      "docker",
      :infrastructure,
      %{
        required: true,
        services: ["neo4j", "dnd-app"],
        description: "Container runtime for local development and deployment"
      }
    )

    DndApp.RiskRegistry.register_risk(
      "docker",
      "Docker daemon not running",
      :high,
      %{
        impact: "Services cannot start",
        mitigation: "Check docker status, provide clear error messages"
      }
    )

    # Docker Compose
    DndApp.RiskRegistry.register_dependency(
      "docker-compose",
      :infrastructure,
      %{
        required: true,
        compose_file: "docker-compose.yml",
        description: "Orchestration tool for multi-container setup"
      }
    )

    # Elixir/OTP
    DndApp.RiskRegistry.register_dependency(
      "elixir",
      :infrastructure,
      %{
        version: "~> 1.14",
        required: true,
        description: "Programming language and runtime"
      }
    )

    DndApp.RiskRegistry.register_risk(
      "elixir",
      "Version incompatibility",
      :medium,
      %{
        impact: "Code may not compile or run correctly",
        mitigation: "Use asdf or similar version manager, document required version"
      }
    )

    # Link infrastructure to application
    DndApp.RiskRegistry.link_to_component("docker", "dnd-app", :application)
    DndApp.RiskRegistry.link_to_component("elixir", "dnd-app", :application)

    IO.puts("  ✓ Registered infrastructure dependencies")
  end

  defp create_dependency_relationships do
    IO.puts("\n🔗 Creating dependency relationships...")

    # Application depends on services
    DndApp.RiskRegistry.add_dependency_relationship("dnd-app", "neo4j", %{
      critical: true,
      description: "Application requires Neo4j for data persistence"
    })

    # Application depends on data sources
    DndApp.RiskRegistry.add_dependency_relationship("dnd-app", "5etools-data", %{
      critical: false,
      description: "Application uses 5etools data for game content"
    })

    # Data import pipeline depends on data source
    DndApp.RiskRegistry.add_dependency_relationship("data-import-pipeline", "5etools-data", %{
      critical: true,
      description: "Import pipeline requires 5etools data files"
    })

    # Data import pipeline depends on Neo4j
    DndApp.RiskRegistry.add_dependency_relationship("data-import-pipeline", "neo4j", %{
      critical: true,
      description: "Import pipeline requires Neo4j to store imported data"
    })

    IO.puts("  ✓ Created dependency relationships")
  end

  # Helper to extract dependencies from mix.exs
  defp get_mix_dependencies do
    # Read mix.exs and extract deps
    mix_file = "mix.exs"

    if File.exists?(mix_file) do
      try do
        {deps, _} = Code.eval_file(mix_file)
        project = deps.project()
        deps_list = project[:deps] || []

        Enum.map(deps_list, fn
          {name, version} when is_binary(version) or is_atom(version) ->
            {name, to_string(version), []}
          {name, opts} when is_list(opts) ->
            version = Keyword.get(opts, :version) || Keyword.get(opts, :git) || "unknown"
            {name, to_string(version), opts}
          {name, version, opts} ->
            {name, to_string(version), opts}
          other ->
            {inspect(other), "unknown", []}
        end)
      rescue
        _ ->
          # Fallback: return empty list if we can't parse
          []
      end
    else
      []
    end
  end
end
