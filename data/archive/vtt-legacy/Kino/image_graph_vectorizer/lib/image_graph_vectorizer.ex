defmodule ImageGraphVectorizer do
  @moduledoc """
  Public API for the Image Graph Vectorizer application.
  """

  alias ImageGraphVectorizer.{DB, Embedder}

  @doc """
  Find images similar to a given image path.
  """
  def find_similar(image_path, limit \\ 10) do
    with {:ok, embedding, _metadata} <- Embedder.generate(image_path),
         {:ok, results} <- DB.Neo4j.find_similar_images(embedding, limit) do
      {:ok, results}
    end
  end

  @doc """
  Get statistics about the image graph.
  """
  def stats do
    DB.Neo4j.get_stats()
  end

  @doc """
  Manually trigger processing of a specific directory.
  """
  def process_directory(path) do
    extensions = Application.get_env(:image_graph_vectorizer, :image_extensions)
    pattern = "*{#{Enum.join(extensions, ",")}}"
    
    Path.join([path, "**", pattern])
    |> Path.wildcard()
    |> Task.async_stream(&ImageGraphVectorizer.Processor.process_file/1,
         max_concurrency: System.schedulers_online())
    |> Stream.run()
  end
end