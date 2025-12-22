ExUnit.start()

# Configure ExUnit
ExUnit.configure(
  exclude: [integration: true],
  formatters: [ExUnit.CLIFormatter]
)




