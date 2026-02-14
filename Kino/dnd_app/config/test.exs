import Config

# Configure your database
config :dnd_app, DndAppWeb.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: 4002],
  server: false

# In test we don't send emails.
config :dnd_app, :test,
  # You can set this to true to enable test mode
  test_mode: true

# Print only warnings and errors during test
config :logger, level: :warn




