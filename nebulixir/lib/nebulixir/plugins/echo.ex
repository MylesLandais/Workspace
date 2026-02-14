defmodule Nebulixir.Commands.Echo do
  # Use the Nebulixir.Plugin behavior helper
  use Nebulixir.Plugin
  require Logger

  @moduledoc """
  A slash command that echoes back the user's input.
  """

  @impl true
  def command_spec do
    %{
      name: "echo",
      description: "Echoes back the message you provide.",
      options: [
        %{
          name: "message",
          description: "What to echo back",
          type: 3, # STRING
          required: false
        }
      ]
    }
  end

  # Implement the new handle_command/2 function
  # It receives the raw interaction struct and the ctx map
  @impl true
  def handle_command(interaction, _ctx) do
    Logger.info("Handling /echo command...")

    # Extract the 'message' option from the interaction data.
    options_list = interaction.data.options || []

    message_option = Enum.find(options_list, fn opt -> opt.name == "message" end)

    message_to_echo = case message_option do
      nil -> "You said: Nothing to echo!" # Default if the option is missing
      %{value: value} -> value # Extract the value from the option map
      _ -> "Error retrieving message option." # Fallback for unexpected structure
    end

    response_content = "#{message_to_echo}"

    # Construct the response data using Nostrum's expected format for Type 4
    response_data = %{ type: 4, data: %{content: response_content} }

    # Send the response using Nostrum API
    case Nostrum.Api.Interaction.create_response(interaction.id, interaction.token, response_data) do
       {:ok, _response_data} ->
         Logger.info("Sent '/echo' response via API!")
       {:ok} -> # <--- Added this clause back!
         Logger.warning("Nostrum API returned {:ok} without response data for interaction ID #{interaction.id}.")
       {:error, reason} ->
         Logger.error("Failed to send '/echo' response via API for interaction ID #{interaction.id}: #{inspect(reason)}")
    end

    :ok # Still return :ok from handle_command
  end
end
