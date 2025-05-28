defmodule Nebulixir.Commands.Ping do
  use Nebulixir.Plugin
  require Logger

  @moduledoc "Responds with Pong!"

  @impl true
  def command_spec do
    %{ name: "ping", description: "Responds with Pong!", options: [] }
  end

  @impl true
  def handle_command(interaction, _ctx) do # Use the interaction passed as the first arg, ignore ctx
    Logger.info("Handling /ping command...")
    response_data = %{ type: 4, data: %{content: "Pong from Elixir Plugin!"} }

    # FIX: Add a case clause to handle the {:ok} tuple specifically
    case Nostrum.Api.Interaction.create_response(interaction.id, interaction.token, response_data) do
       {:ok, _response_data} -> # Added _response_data to indicate we might not need the response data itself
         Logger.info("Sent 'Pong!' response via API!")
       {:ok} -> # <-- ADD THIS CLAUSE
         Logger.warning("Nostrum API returned {:ok} without response data for interaction ID #{interaction.id}.")
       {:error, reason} ->
         Logger.error("Failed to send 'Pong!' via API for interaction ID #{interaction.id}: #{inspect(reason)}")
    end
    :ok
  end
end
