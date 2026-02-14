defmodule DndApp.Application do
  @moduledoc false
  use Application

  @impl true
  def start(_type, _args) do
    neo4j_config = Application.get_env(:dnd_app, DndApp.DB.Neo4j, [])

    children = [
      # Start the Telemetry supervisor
      DndAppWeb.Telemetry,
      # Start the PubSub system
      {Phoenix.PubSub, name: DndApp.PubSub},
      # Start Neo4j connection (with restart: :transient to allow graceful failure)
      {DndApp.DB.Neo4j, neo4j_config},
      # Start the Endpoint (http/https)
      DndAppWeb.Endpoint
    ]

    # Use one_for_one with increased restart limits to handle transient failures
    # Increased limits allow Neo4j connection retries without shutting down the app
    opts = [
      strategy: :one_for_one,
      name: DndApp.Supervisor,
      max_restarts: 10,
      max_seconds: 30
    ]
    case Supervisor.start_link(children, opts) do
      {:ok, _pid} = result ->
        # Initialize schema asynchronously after app starts
        Task.start(fn -> initialize_neo4j_schema() end)
        result
      error ->
        error
    end
  end

  defp initialize_neo4j_schema do
    # Delay to ensure connection pool is fully initialized
    Process.sleep(2000)

    case DndApp.DB.Neo4j.setup_schema() do
      :ok ->
        require Logger
        Logger.info("Neo4j schema initialized successfully")
      {:error, reason} ->
        require Logger
        Logger.error("Failed to initialize Neo4j schema: #{inspect(reason)}")
        # Continue anyway - schema might already exist
    end
  end

  @impl true
  def config_change(changed, _new, removed) do
    DndAppWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end
