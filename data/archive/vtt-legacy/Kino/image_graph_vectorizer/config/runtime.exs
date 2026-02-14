import Config

# Runtime configuration that can be overridden at runtime
if config_env() == :prod do
  # In production, we might want to read from environment variables
  # or use different configuration values
  
  config :image_graph_vectorizer,
    # Production-specific settings
    watch_dir: System.get_env("WATCH_DIR", "/var/lib/images"),
    embedding_api: System.get_env("EMBEDDING_API", "http://embedding-service:8100/v1/embeddings")
end