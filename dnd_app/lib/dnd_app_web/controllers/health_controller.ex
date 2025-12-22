defmodule DndAppWeb.HealthController do
  use DndAppWeb, :controller
  alias DndApp.DB.Neo4j

  def check(conn, _params) do
    status = %{
      status: "ok",
      phoenix: "running",
      timestamp: DateTime.utc_now() |> DateTime.to_iso8601()
    }

    status = check_neo4j(status)
    status = check_schema(status)

    http_status = if status.status == "ok", do: 200, else: 503

    conn
    |> put_status(http_status)
    |> json(status)
  end

  defp check_neo4j(status) do
    try do
      # Try a simple query to verify connection
      case Neo4j.query("RETURN 1 as test") do
        {:ok, _} ->
          Map.put(status, :neo4j, "connected")

        error ->
          Map.merge(status, %{
            status: "degraded",
            neo4j: "disconnected",
            neo4j_error: inspect(error)
          })
      end
    rescue
      e ->
        Map.merge(status, %{
          status: "degraded",
          neo4j: "error",
          neo4j_error: Exception.message(e)
        })
    end
  end

  defp check_schema(status) do
    try do
      # Check if schema constraints exist (indicates schema is initialized)
      case Neo4j.query("SHOW CONSTRAINTS") do
        {:ok, constraints} when is_list(constraints) ->
          constraint_count = length(constraints)
          Map.put(status, :schema, %{status: "ready", constraints: constraint_count})

        {:ok, _} ->
          Map.put(status, :schema, %{status: "unknown"})

        error ->
          Map.put(status, :schema, %{
            status: "error",
            error: inspect(error)
          })
      end
    rescue
      e ->
        Map.put(status, :schema, %{
          status: "error",
          error: Exception.message(e)
        })
    end
  end
end
