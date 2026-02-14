import Config

# The runtime configuration is executed on the server before the
# application starts. It is typically used to load production configuration
# and secrets from environment variables or elsewhere. Do not define any
# Elixir code here, as it won't be executed.

if config_env() == :prod do
  # The secret key base is used to sign/encrypt cookies and other secrets.
  # A default value is used in config/dev.exs and config/test.exs which
  # is fine for development and test, but something unique and random is required
  # for production.

  secret_key_base =
    System.get_env("SECRET_KEY_BASE") ||
      raise """
      environment variable SECRET_KEY_BASE is missing.
      You can generate one by calling: mix phx.gen.secret
      """

  host = System.get_env("PHX_HOST") || "example.com"
  port = String.to_integer(System.get_env("PORT") || "4000")

  config :dnd_app, DndAppWeb.Endpoint,
    url: [host: host, port: 443, scheme: "https"],
    http: [
      ip: {0, 0, 0, 0, 0, 0, 0, 0},
      port: port
    ],
    secret_key_base: secret_key_base

  # Neo4j configuration from environment
  config :dnd_app, DndApp.DB.Neo4j,
    url: System.get_env("NEO4J_URL") || "bolt://localhost:7687",
    username: System.get_env("NEO4J_USER") || "neo4j",
    password: System.get_env("NEO4J_PASSWORD") || "password",
    pool_size: String.to_integer(System.get_env("NEO4J_POOL_SIZE") || "10"),
    max_overflow: String.to_integer(System.get_env("NEO4J_MAX_OVERFLOW") || "5")
end
