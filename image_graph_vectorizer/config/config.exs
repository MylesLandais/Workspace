import Config

# Neo4j Configuration
config :bolt_sips, Bolt,
  url: "bolt://localhost:7687",
  basic_auth: [username: "neo4j", password: "password"],
  pool_size: 10,
  max_overflow: 5

# Image Vectorizer Configuration
config :image_graph_vectorizer,
  # Directory to watch for images
  watch_dir: System.get_env("WATCH_DIR", "/path/to/images"),
  
  # Embedding API endpoint
  embedding_api: System.get_env("EMBEDDING_API", "http://localhost:8100/v1/embeddings"),
  
  # Vector dimensions (CLIP typically uses 512 or 768)
  vector_dimensions: String.to_integer(System.get_env("VECTOR_DIM", "768")),
  
  # Supported image extensions
  image_extensions: [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
  
  # Batch size for processing
  batch_size: 50,
  
  # Processing timeout (ms)
  processing_timeout: 30_000

# Environment-specific configuration
import_config "#{config_env()}.exs"