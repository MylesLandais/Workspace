defmodule Nebulixir.Commands.Play do
  @moduledoc """
  Plays audio from YouTube or a direct audio link in your current voice channel.
  Accepts a direct YouTube URL or keyword search (ytsearch).
  """

  use Nebulixir.Plugin
  require Logger

  alias Nostrum.Api.Interaction
  alias Nostrum.Cache.GuildCache
  alias Nostrum.Voice

  @youtube_regex ~r{^(https?://)?(www\.)?(youtube\.com|youtu\.be)/}

  @impl true
  def command_spec do
    %{
      name: "play",
      description: "Play audio from a YouTube URL or search keywords",
      options: [
        %{type: 3, name: "query", description: "YouTube URL or search terms", required: true}
      ]
    }
  end

  @impl true
  def handle_command(
        %{id: id, token: token, guild_id: guild_id,
          member: %{user_id: user_id},
          data: %{options: [%{value: query}]}}
        = _interaction,
        _ctx
      ) do
    Logger.info("[Play] /play #{query} by #{user_id} in guild #{guild_id}")

    # Defer response to avoid 3s timeout
    Interaction.create_response(id, token, %{type: 5})

    case current_voice_channel(guild_id, user_id) do
      nil ->
        Interaction.create_followup_message(token, %{content: "❌ You are not in a voice channel!", flags: 64})

      channel_id ->
        if Voice.get_channel_id(guild_id) != channel_id do
          Logger.info("[Play] Joining voice channel #{channel_id}")
          Voice.join_channel(guild_id, channel_id)
        else
          Logger.info("[Play] Already in channel #{channel_id}, skipping join")
        end

        if wait_until_ready(guild_id, 10) do
          {audio_source, provider} =
            cond do
              Regex.match?(@youtube_regex, query) ->
                {query, :ytdl}
              String.starts_with?(query, "http") && String.contains?(query, [".mp3", ".wav", ".ogg", ".flac"]) ->
                {query, :url}
              true ->
                {"ytsearch:#{query}", :ytdl}
            end

          Logger.info("[Play] Voice.play: #{inspect(audio_source)}, provider: #{provider}")

          result = Voice.play(guild_id, audio_source, provider)
          Logger.info("[Play] Voice.play/3 result: #{inspect(result)}")

          feedback =
            cond do
              provider == :ytdl and String.starts_with?(audio_source, "ytsearch:") ->
                "🔍 Searching and playing best match for: #{query}"
              provider == :ytdl ->
                "▶️ Now playing: #{query}"
              provider == :url ->
                "▶️ Now playing audio file: #{query}"
            end

          Interaction.create_followup_message(token, %{content: feedback})
        else
          Logger.error("[Play] Voice connection not ready in guild #{guild_id}")
          Interaction.create_followup_message(token, %{content: "❌ Failed to join your voice channel.", flags: 64})
        end
    end

    :ok
  end

  # Find the voice channel of a user in a guild
  defp current_voice_channel(guild_id, user_id) do
    GuildCache.get!(guild_id)
    |> Map.get(:voice_states, [])
    |> Enum.find(fn vs -> vs.user_id == user_id end)
    |> case do
      nil -> nil
      vs -> vs.channel_id
    end
  end

  # Poll until the voice connection is ready
  defp wait_until_ready(_guild, 0), do: false
  defp wait_until_ready(guild, attempts) when attempts > 0 do
    if Voice.ready?(guild) do
      true
    else
      :timer.sleep(500)
      wait_until_ready(guild, attempts - 1)
    end
  end
end
