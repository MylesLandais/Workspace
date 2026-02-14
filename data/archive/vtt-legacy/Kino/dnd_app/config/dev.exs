import Config

# Configure your database
config :dnd_app,
  # Enable hot reloading
  code_reloader: true,
  debug_errors: true,
  check_origin: false

# For development, we disable any cache and enable
# debugging and code reloading.
config :dnd_app, DndAppWeb.Endpoint,
  # Binding to 0.0.0.0 allows access from outside the container
  http: [ip: {0, 0, 0, 0}, port: 4000],
  # Secret key base for development (use a long random string in production)
  secret_key_base: "dev_secret_key_base_change_in_production_use_mix_phx_gen_secret_to_generate_one",
  # Enable code reloading
  live_reload: [
    patterns: [
      ~r"priv/static/.*(js|css|png|jpeg|jpg|gif|svg)$",
      ~r"priv/gettext/.*(po)$",
      ~r"lib/dnd_app_web/(controllers|live|components|views)/.*(ex)$",
      ~r"lib/dnd_app_web/templates/.*(eex)$",
      ~r"assets/js/.*(ts|tsx)$"
    ]
  ]

# Asset compilation is handled by Bun
# Run `bun run watch` in the assets directory for automatic rebuilding
# Or use the optional watcher configuration below (requires bun mix task):
# watchers: [
#   bun: {Bun, :install_and_run, [:default, ~w(run watch)]}
# ]

# Do not include metadata nor timestamps in development logs
config :logger, :console, format: "[$level] $message\n"

# Set a higher log level in development
config :logger, level: :debug
