defmodule ImageGraphVectorizer.Processor do
  @moduledoc """
  Core image processing logic - generates embeddings and stores in Neo4j.
  """
  require Logger
  alias ImageGraphVectorizer.{Embedder, DB}

  @doc """
  Process a single image file: generate embedding and store in graph.
  """
  def process_file(path) do
    Logger.debug("Processing: #{path}")
    
    # Extract topic from folder name (like the Python script)
    topic = extract_topic(path)
    
    case Embedder.generate(path) do
      {:ok, vector, metadata} ->
        case DB.Neo4j.upsert_image(path, topic, vector, metadata) do
          {:ok, _} ->
            Logger.info("✓ Vectorized and stored: #{Path.basename(path)} (#{topic})")
            :ok
            
          {:error, reason} ->
            Logger.error("✗ DB Error for #{path}: #{inspect(reason)}")
            {:error, reason}
        end
        
      {:error, reason} ->
        Logger.error("✗ Failed to embed #{path}: #{inspect(reason)}")
        {:error, reason}
    end
  end

  defp extract_topic(path) do
    path
    |> Path.dirname()
    |> Path.basename()
  end
end