defmodule ImageGraphVectorizer.DB.Neo4j do
  @moduledoc """
  Neo4j database operations for graph-based image storage.
  Implements idempotent operations using MERGE.
  """
  require Logger
  alias Bolt.Sips, as: Neo

  @doc """
  Initialize Neo4j schema with constraints and vector indexes.
  This is idempotent and safe to run multiple times.
  """
  def setup_schema do
    dims = Application.get_env(:image_graph_vectorizer, :vector_dimensions)
    
    with {:ok, _} <- create_constraints(),
         {:ok, _} <- create_vector_index(dims) do
      :ok
    else
      error -> {:error, error}
    end
  end

  defp create_constraints do
    queries = [
      # Unique constraint on image path
      """
      CREATE CONSTRAINT image_path_unique IF NOT EXISTS
      FOR (i:Image) REQUIRE i.path IS UNIQUE
      """,
      
      # Unique constraint on topic name
      """
      CREATE CONSTRAINT topic_name_unique IF NOT EXISTS
      FOR (t:Topic) REQUIRE t.name IS UNIQUE
      """
    ]

    Enum.reduce_while(queries, {:ok, nil}, fn query, _acc ->
      case Neo.query(Neo.conn(), query) do
        {:ok, result} -> {:cont, {:ok, result}}
        error -> {:halt, error}
      end
    end)
  end

  defp create_vector_index(dims) do
    query = """
    CREATE VECTOR INDEX image_embeddings IF NOT EXISTS
    FOR (i:Image) ON (i.embedding)
    OPTIONS {
      indexConfig: {
        `vector.dimensions`: #{dims},
        `vector.similarity_function`: 'cosine'
      }
    }
    """
    
    Neo.query(Neo.conn(), query)
  end

  @doc """
  Upsert an image node with its vector embedding.
  Creates relationships to Topic nodes.
  """
  def upsert_image(path, topic, embedding, metadata \\ %{}) do
    cypher = """
    // Create or update the Image node
    MERGE (i:Image {path: $path})
    SET i.embedding = $embedding,
        i.updated_at = datetime(),
        i.size_kb = $size_kb,
        i.format = $format
    
    // Create or get the Topic node
    MERGE (t:Topic {name: $topic})
    ON CREATE SET t.created_at = datetime()
    
    // Create relationship between Image and Topic
    MERGE (i)-[r:BELONGS_TO]->(t)
    ON CREATE SET r.created_at = datetime()
    
    RETURN i, t
    """
    
    params = %{
      path: path,
      topic: topic,
      embedding: embedding,
      size_kb: Map.get(metadata, :size_kb, 0),
      format: Map.get(metadata, :format, "unknown")
    }
    
    case Neo.query(Neo.conn(), cypher, params) do
      {:ok, result} ->
        Logger.info("Upserted image: #{path}")
        {:ok, result}
      error ->
        Logger.error("Failed to upsert image #{path}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Delete an image node and its relationships.
  """
  def delete_image(path) do
    cypher = """
    MATCH (i:Image {path: $path})
    DETACH DELETE i
    """
    
    case Neo.query(Neo.conn(), cypher, %{path: path}) do
      {:ok, _} ->
        Logger.info("Deleted image: #{path}")
        :ok
      error ->
        Logger.error("Failed to delete image #{path}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Find similar images using vector similarity search.
  """
  def find_similar_images(embedding, limit \\ 10) do
    cypher = """
    CALL db.index.vector.queryNodes('image_embeddings', $limit, $embedding)
    YIELD node, score
    MATCH (node)-[:BELONGS_TO]->(t:Topic)
    RETURN node.path as path, 
           node.updated_at as updated_at,
           t.name as topic,
           score
    ORDER BY score DESC
    """
    
    Neo.query(Neo.conn(), cypher, %{embedding: embedding, limit: limit})
  end

  @doc """
  Get statistics about the image graph.
  """
  def get_stats do
    cypher = """
    MATCH (i:Image)
    OPTIONAL MATCH (t:Topic)
    OPTIONAL MATCH (i)-[:BELONGS_TO]->(t)
    RETURN 
      count(DISTINCT i) as total_images,
      count(DISTINCT t) as total_topics,
      count(DISTINCT i)-[:BELONGS_TO]->() as images_with_topics
    """
    
    Neo.query(Neo.conn(), cypher)
  end
end