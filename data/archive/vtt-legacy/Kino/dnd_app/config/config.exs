import Config

# Asset compilation is handled by Bun (see assets/build.ts)
# To build assets:
#   - Development: `cd assets && bun run watch` (runs in watch mode)
#   - Production: `cd assets && bun run build` or `mix assets.deploy`
#
# Bun provides native TypeScript support and faster builds than esbuild/tailwind mix tasks.
# The build process compiles TypeScript from assets/js/app.ts and processes Tailwind CSS.

# Configure esbuild (the version is required)
# Commented out - Bun handles asset compilation instead
# config :esbuild,
#   version: "0.17.11",
#   default: [
#     args:
#       ~w(js/app.js --bundle --target=es2017 --outdir=../priv/static/assets --external:/fonts/* --external:/images/*),
#     cd: Path.expand("../assets", __DIR__),
#     env: %{"NODE_PATH" => Path.expand("../deps", __DIR__)}
#   ]

# Configure tailwind (the version is required)
# Commented out - Bun handles Tailwind CSS compilation instead
# config :tailwind,
#   version: "3.3.0",
#   default: [
#     args: ~w(
#       --config=tailwind.config.js
#       --input=css/app.css
#       --output=../priv/static/assets/app.css
#     ),
#     cd: Path.expand("../assets", __DIR__)
#   ]

# Configures the endpoint
config :dnd_app, DndAppWeb.Endpoint,
  url: [host: "localhost"],
  adapter: Phoenix.Endpoint.Cowboy2Adapter,
  render_errors: [
    formats: [html: DndAppWeb.ErrorHTML, json: DndAppWeb.ErrorJSON],
    layout: false
  ],
  pubsub_server: DndApp.PubSub,
  live_view: [signing_salt: "dnd_app_secret"]

# Configures Elixir's Logger
config :logger, :console,
  format: "$time $metadata[$level] $message\n",
  metadata: [:request_id]

# Use Jason for JSON parsing in Phoenix
config :phoenix, :json_library, Jason

# Neo4j Configuration
# Supports both local development (localhost) and devcontainer (neo4j service name)
# Environment variables override defaults for devcontainer compatibility
config :dnd_app, DndApp.DB.Neo4j,
  url: System.get_env("NEO4J_URL") || "bolt://localhost:7687",
  username: System.get_env("NEO4J_USER") || "neo4j",
  password: System.get_env("NEO4J_PASSWORD") || "password",
  pool_size: 10,
  max_overflow: 5

# Import environment specific config. This must remain at the bottom
# of this file so it overrides the configuration defined above.
import_config "#{config_env()}.exs"
