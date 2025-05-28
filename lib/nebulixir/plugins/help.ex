defmodule Nebulixir.Commands.Help do
  use Nebulixir.Plugin
  require Logger

  @moduledoc """
  Lists all available commands loaded via the plugin manager.
  """

  @impl true
  def command_spec do
    %{ name: "help", description: "List all available commands", options: [] }
  end

  @impl true
  def handle_command(interaction, %{plugins: commands}) do
    Logger.info("Handling /help command for interaction ID #{interaction.id}...")


    help_text =
      commands
      |> Enum.map(fn %{name: name, description: desc} -> "`/#{name}` – #{desc}" end)
      |> Enum.join("\n")

    content = if help_text == "" do
      "No commands available."
    else
      "**Available Commands:**\n" <> help_text
    end

    response_data = %{ type: 4, data: %{content: content} }

    case Nostrum.Api.Interaction.create_response(interaction.id, interaction.token, response_data) do
       {:ok, _response_data} -> # Handle {:ok, response}
         Logger.info("Sent help response via API for interaction ID #{interaction.id}.")
       {:ok} -> # Handle just {:ok} (carried over from previous fix)
         Logger.warning("Nostrum API returned {:ok} without response data for interaction ID #{interaction.id}.")
       {:error, reason} -> # Handle {:error, reason}
         Logger.error("Failed to send help via API for interaction ID #{interaction.id}: #{inspect(reason)}")
    end
    :ok
  end
end
