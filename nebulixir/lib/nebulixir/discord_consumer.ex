defmodule Nebulixir.DiscordConsumer do
  use Nostrum.Consumer
  require Logger

  # --- Event Handling ---

  @impl true
  def handle_event({:READY, %{user: user}, _ws_state}) do
    Logger.info("[green]Bot ready! Logged in as: #{user.username}##{user.discriminator}[/green]")

    Task.start(fn ->
      :timer.sleep(1000)
      Logger.info("Registering slash commands...")
      Nebulixir.PluginManager.sync_commands()
    end)


    :ok
  end

  @impl true
  def handle_event({:INTERACTION_CREATE, interaction, _ws_state}) do

    if interaction.type == Nostrum.Constants.InteractionType.application_command do
      command_data = interaction.data
      Nebulixir.PluginManager.dispatch_command(command_data.name, interaction, %{consumer: self()})
    end

    :ok
  end

  @impl true
  def handle_event(_event), do: :ignore

  @impl true
  def handle_call({:send_response, interaction_id, interaction_token, data}, _from, state) do
    #Logger.debug("Handling request to send interaction response via API.")
    result = Nostrum.Api.Interaction.create_response(interaction_id, interaction_token, data)

    case result do
      {:ok, _response_data} ->
        Logger.info("Successfully sent interaction response via API.")
      {:error, reason} ->
        Logger.error("Failed to send interaction response via API: #{inspect(reason)}")
    end

    {:reply, result, state}
  end

  @impl true
  def handle_call({:send_followup, interaction_token, _wait, params}, _from, state) do
    #Logger.debug("Handling request to send followup message via API.")
    result = Nostrum.Api.Interaction.create_followup_message(interaction_token, params)
    {:reply, result, state}
  end

  @impl true
  def handle_call({:edit_original_response, interaction_token, params}, _from, state) do
    #Logger.debug("Handling request to edit original response via API.")
    result = Nostrum.Api.Interaction.edit_response(interaction_token, params)
    {:reply, result, state}
  end

  @impl true
  def handle_call(_request, _from, state) do
    #Logger.warning("Received unhandled call request in DiscordConsumer: #{inspect(request)}")
    {:reply, {:error, :unhandled_call}, state}
  end
end
