defmodule ImageGraphVectorizer.Application do
  @moduledoc """
  Main application supervisor that coordinates all services.
  """
  use Application
  require Logger

  @impl true
  def start(_type, _args) do
    Logger.info("Starting ImageGraphVectorizer Application...")

    # Initialize Neo4j schema before starting workers
    case ImageGraphVectorizer.DB.Neo4j.setup_schema() do
      :ok ->
        Logger.info("Neo4j schema initialized successfully")
      {:error, reason} ->
        Logger.error("Failed to initialize Neo4j schema: #{inspect(reason)}")
        # Continue anyway - schema might already exist
    end

    children = [
      # Neo4j Connection Pool
      {Bolt.Sips, Application.get_env(:bolt_sips, Bolt)},
      
      # File System Watcher (Hot Reload)
      ImageGraphVectorizer.Watcher,
      
      # Image Processor (with Task.Supervisor for parallel processing)
      {Task.Supervisor, name: ImageGraphVectorizer.TaskSupervisor}
    ]

    opts = [strategy: :one_for_one, name: ImageGraphVectorizer.Supervisor]
    Supervisor.start_link(children, opts)
  end
end