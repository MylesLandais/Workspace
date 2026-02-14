defmodule Nebulixir.Application do
  use Application

  @impl true
  def start(_type, _args) do
    children = [
      Nebulixir.PluginManager,
      Nebulixir.DiscordConsumer # This consumer will now receive events once Nostrum is started
    ]

    # Keep the supervisor opts
    opts = [strategy: :one_for_one, name: Nebulixir.Supervisor]
    Supervisor.start_link(children, opts)
  end

end
