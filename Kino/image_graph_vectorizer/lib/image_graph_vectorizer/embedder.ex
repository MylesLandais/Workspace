defmodule ImageGraphVectorizer.Embedder do
  @moduledoc """
  Handles image encoding and embedding generation via external API.
  Replicates the Python encode_image_to_base64 and get_embedding logic.
  """
  require Logger

  @doc """
  Generate embedding vector for an image file.
  """
  def generate(file_path) do
    with {:ok, metadata} <- extract_metadata(file_path),
         {:ok, binary} <- File.read(file_path),
         base64 <- Base.encode64(binary),
         {:ok, embedding} <- call_embedding_api(base64) do
      {:ok, embedding, metadata}
    else
      {:error, :enoent} ->
        {:error, "File not found: #{file_path}"}
      {:error, reason} = error ->
        Logger.error("Failed to generate embedding for #{file_path}: #{inspect(reason)}")
        error
    end
  end

  defp extract_metadata(file_path) do
    with {:ok, %File.Stat{size: size}} <- File.stat(file_path) do
      format = file_path |> Path.extname() |> String.trim_leading(".")
      
      metadata = %{
        size_kb: div(size, 1024),
        format: format
      }
      
      {:ok, metadata}
    end
  end

  defp call_embedding_api(base64_string) do
    url = Application.get_env(:image_graph_vectorizer, :embedding_api)
    timeout = Application.get_env(:image_graph_vectorizer, :processing_timeout)
    
    payload = %{
      "image_base64" => [base64_string],
      "image_urls" => []
    }

    case Req.post(url, json: payload, receive_timeout: timeout) do
      {:ok, %{status: 200, body: %{"embeddings" => [vector | _]}}} ->
        {:ok, vector}
        
      {:ok, %{status: status, body: body}} ->
        {:error, "API returned status #{status}: #{inspect(body)}"}
        
      {:error, %{reason: :timeout}} ->
        {:error, "Embedding API timeout after #{timeout}ms"}
        
      {:error, reason} ->
        {:error, "HTTP request failed: #{inspect(reason)}"}
    end
  end

  @doc """
  Batch process multiple images efficiently.
  """
  def generate_batch(file_paths) do
    batch_size = Application.get_env(:image_graph_vectorizer, :batch_size)
    
    file_paths
    |> Enum.chunk_every(batch_size)
    |> Enum.flat_map(fn batch ->
      batch
      |> Task.async_stream(&generate/1, 
           max_concurrency: System.schedulers_online(),
           timeout: :infinity)
      |> Enum.to_list()
    end)
  end
end