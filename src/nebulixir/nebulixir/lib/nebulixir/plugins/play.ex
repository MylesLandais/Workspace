defmodule Nebulixir.Commands.Play do
  @moduledoc """
  Plays audio from YouTube or direct links with queue.
  Shows the real song title as bot status.
  Leaves voice channel after 5 minutes idle.
  """

  use Nebulixir.Plugin
  require Logger

  alias Nostrum.Api.Interaction
  alias Nostrum.Cache.GuildCache
  alias Nostrum.Voice

  @youtube_regex ~r{^(https?://)?(www\.)?(youtube\.com|youtu\.be)/}

  ## --- AGENTS ---
  defp queue_agent do
    case Process.whereis(__MODULE__.QueueAgent) do
      nil -> {:ok, _} = Agent.start_link(fn -> %{} end, name: __MODULE__.QueueAgent); __MODULE__.QueueAgent
      _ -> __MODULE__.QueueAgent
    end
  end

  defp player_pid_agent do
    case Process.whereis(__MODULE__.PlayerPidAgent) do
      nil -> {:ok, _} = Agent.start_link(fn -> %{} end, name: __MODULE__.PlayerPidAgent); __MODULE__.PlayerPidAgent
      _ -> __MODULE__.PlayerPidAgent
    end
  end

  defp leave_timer_agent do
    case Process.whereis(__MODULE__.LeaveTimerAgent) do
      nil -> {:ok, _} = Agent.start_link(fn -> %{} end, name: __MODULE__.LeaveTimerAgent); __MODULE__.LeaveTimerAgent
      _ -> __MODULE__.LeaveTimerAgent
    end
  end

  ## --- QUEUE LOGIC ---
  defp get_queue(guild_id), do: Agent.get(queue_agent(), &Map.get(&1, guild_id, []))
  defp add_to_queue(guild_id, item), do: Agent.update(queue_agent(), fn qs -> Map.update(qs, guild_id, [item], &(&1 ++ [item])) end)
  defp pop_queue(guild_id), do: Agent.get_and_update(queue_agent(), fn qs -> case Map.get(qs, guild_id, []) do [h|t] -> { {:ok, h}, Map.put(qs, guild_id, t) }; [] -> {:empty, qs} end end)

  defp set_player_pid(guild_id, pid), do: Agent.update(player_pid_agent(), &Map.put(&1, guild_id, pid))
  defp get_player_pid(guild_id), do: Agent.get(player_pid_agent(), &Map.get(&1, guild_id))

  ## --- LEAVE TIMER LOGIC ---
  defp schedule_leave(guild_id, channel_id) do
    Logger.info("[Play] Scheduling auto-leave for #{guild_id} in 5 minutes...")
    cancel_leave(guild_id)
    timer = Process.send_after(self(), {:auto_leave, guild_id, channel_id}, 5 * 60 * 1000)
    Agent.update(leave_timer_agent(), &Map.put(&1, guild_id, timer))
  end
  defp cancel_leave(guild_id) do
    Agent.get_and_update(leave_timer_agent(), fn timers ->
      case Map.pop(timers, guild_id) do
        {nil, rest} -> {nil, rest}
        {timer_ref, rest} -> Process.cancel_timer(timer_ref); {timer_ref, rest}
      end
    end)
    :ok
  end

  ## --- DISCORD INTERFACE ---
  @impl true
  def command_spec do
    %{
      name: "play",
      description: "Play audio from a YouTube URL or search keywords (with queueing, real song title)",
      options: [
        %{type: 3, name: "query", description: "YouTube URL or search terms", required: true}
      ]
    }
  end

  @impl true
  def handle_command(
        %{id: id, token: token, guild_id: guild_id,
          member: %{user_id: user_id},
          data: %{options: [%{value: query}]}} = _interaction,
        _ctx
      ) do
    Logger.info("[Play] /play #{query} by #{user_id} in guild #{guild_id}")

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

        cancel_leave(guild_id) # Cancel pending auto-leave

        if wait_until_ready(guild_id, 10) do
          song = %{query: query, user_id: user_id, token: token}
          add_to_queue(guild_id, song)
          Logger.info("[Play] Added to queue. Queue: #{inspect(get_queue(guild_id))}")

          # If queue length is 1 and nothing is playing, start playing
          if length(get_queue(guild_id)) == 1 and get_player_pid(guild_id) == nil do
            play_next(guild_id)
            Interaction.create_followup_message(token, %{content: "▶️ Now playing (queue started): #{query}"})
          else
            Interaction.create_followup_message(token, %{content: "⏳ Added to the queue at position #{length(get_queue(guild_id))}."})
          end
        else
          Logger.error("[Play] Voice connection not ready in guild #{guild_id}")
          Interaction.create_followup_message(token, %{content: "❌ Failed to join your voice channel.", flags: 64})
        end
    end

    :ok
  end

  ## --- SMART QUEUE ADVANCEMENT LOGIC (POLLING-BASED) ---
  defp play_next(guild_id) do
    case pop_queue(guild_id) do
      {:ok, %{query: query, token: token}} ->
        {audio_source, provider} =
          cond do
            Regex.match?(@youtube_regex, query) -> {query, :ytdl}
            String.starts_with?(query, "http") && String.contains?(query, [".mp3", ".wav", ".ogg", ".flac"]) -> {query, :url}
            true -> {"ytsearch:#{query}", :ytdl}
          end

        Logger.info("[Play] Voice.play: #{inspect(audio_source)}, provider: #{provider}")

        # Get the YouTube or ytsearch title if ytdl, otherwise just use query
        title =
          if provider == :ytdl do
            youtube_title(audio_source)
          else
            query
          end

        pid =
          spawn(fn ->
            Voice.play(guild_id, audio_source, provider)
            :timer.sleep(1000)
            wait_for_end(guild_id)
            set_player_pid(guild_id, nil)
            play_next(guild_id)
          end)

        set_player_pid(guild_id, pid)

        # --- Set bot status to "Playing: <title>" ---
        Nostrum.Api.Self.update_status(
          "online",
          [%{type: 0, name: "Playing: #{title}"}],
          nil,
          false
        )

        Interaction.create_followup_message(token, %{content: "▶️ Now playing: #{title}"})

      :empty ->
        set_player_pid(guild_id, nil)

        # --- Clear status when not playing ---
        Nostrum.Api.Self.update_status(
          "online",
          [],
          nil,
          false
        )

        check_and_schedule_auto_leave(guild_id)
        :ok
    end
  end

  defp wait_for_end(guild_id) do
    if Voice.playing?(guild_id) do
      :timer.sleep(1000)
      wait_for_end(guild_id)
    else
      :ok
    end
  end

  # --- Get the title using yt-dlp (must be installed and in $PATH)
  defp youtube_title(query) do
    cmd = [
      "yt-dlp",
      "--no-playlist",
      "--skip-download",
      "--print", "%(title)s",
      query
    ]
    # Use List.first(cmd) and tl(cmd) to avoid range warning
    case System.cmd(List.first(cmd), tl(cmd), stderr_to_stdout: true) do
      {title, 0} -> String.trim(title)
      {_err, _} -> query
    end
  end

  # Called after queue is empty or no more users
  defp check_and_schedule_auto_leave(guild_id) do
    channel_id = Voice.get_channel_id(guild_id)
    if channel_id do
      users = current_channel_users(guild_id, channel_id)
      if length(users) <= 1 do
        schedule_leave(guild_id, channel_id)
      end
    end
  end

  ## --- UTILITIES ---
  defp current_voice_channel(guild_id, user_id) do
    GuildCache.get!(guild_id)
    |> Map.get(:voice_states, [])
    |> Enum.find(fn vs -> vs.user_id == user_id end)
    |> case do
      nil -> nil
      vs -> vs.channel_id
    end
  end

  defp current_channel_users(guild_id, channel_id) do
    GuildCache.get!(guild_id)
    |> Map.get(:voice_states, [])
    |> Enum.filter(fn vs -> vs.channel_id == channel_id end)
    |> Enum.map(& &1.user_id)
  end

  defp wait_until_ready(_guild, 0), do: false
  defp wait_until_ready(guild, attempts) when attempts > 0 do
    if Voice.ready?(guild) do
      true
    else
      :timer.sleep(500)
      wait_until_ready(guild, attempts - 1)
    end
  end

  ## --- PROCESS HANDLERS ---
  # Handles auto leave after 5 minutes
  def handle_info({:auto_leave, guild_id, channel_id}, _state) do
    # Check one last time before leaving
    users = current_channel_users(guild_id, channel_id)
    if length(users) <= 1 do
      Logger.info("[Play] Leaving voice channel #{channel_id} in guild #{guild_id} (empty 5 min)")
      Voice.leave_channel(guild_id)
    else
      Logger.info("[Play] Cancelled auto-leave for guild #{guild_id}; users rejoined.")
    end
    :noreply
  end
end
