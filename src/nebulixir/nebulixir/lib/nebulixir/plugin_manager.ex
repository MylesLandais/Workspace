defmodule Nebulixir.PluginManager do
  use GenServer
  require Logger

  @moduledoc """
  Loads and manages command plugins by scanning the source directory.
  Supports hot-reloading via file system watcher.
  Handles Discord slash command syncing.
  """

  @plugin_source_namespace Nebulixir.Commands
  @plugin_source_dir "lib/nebulixir/plugins"

  ## Public API

  def start_link(_opts), do: GenServer.start_link(__MODULE__, %{}, name: __MODULE__)

  def list_commands, do: GenServer.call(__MODULE__, :list_commands)

  def dispatch_command(name, interaction, ctx \\ %{}), do: GenServer.cast(__MODULE__, {:dispatch_command, name, interaction, ctx})

  def reload, do: (Logger.debug("Public API received reload/0 call. Sending :reload cast."); GenServer.cast(__MODULE__, :reload))

  def sync_commands, do: (Logger.debug("Public API received sync_commands/0 call. Sending :do_sync_commands cast."); GenServer.cast(__MODULE__, :do_sync_commands))

  @impl true
  def init(_) do
    Logger.info("Initializing plugin manager...")

    Process.flag(:trap_exit, true)

    state = load_plugins() # Load plugins initially

    abs_plugin_source_dir = Path.expand(@plugin_source_dir)

    # Ensure the directory exists
    unless File.dir?(abs_plugin_source_dir) do
      Logger.error("Plugin source directory does not exist: #{abs_plugin_source_dir}")
      {:ok, state}
    else
      watcher_options = [dirs: [abs_plugin_source_dir], recursive: true]

      Logger.info("Attempting to start watcher for directory: #{inspect(abs_plugin_source_dir)}")
      Logger.info("Directory contents: #{inspect(File.ls!(abs_plugin_source_dir))}")

      result = FileSystem.start_link(watcher_options)
      #Logger.info("FileSystem.start_link result: #{inspect(result)}")

      case result do
        {:ok, watcher_pid} ->
          Logger.info("Watcher started successfully with PID #{inspect(watcher_pid)}")
          # Link to the watcher so we get notified if it dies
          Process.link(watcher_pid)

          # Subscribe to file events
          FileSystem.subscribe(watcher_pid)
          Logger.info("Subscribed to file system events from watcher PID #{inspect(watcher_pid)}")

          {:ok, Map.put(state, :watcher_pid, watcher_pid)}

        {:error, reason} ->
          Logger.error("Failed to start file system watcher: #{inspect(reason)}. Hot-reloading disabled.")
          {:ok, state}

        :ignore ->
          Logger.warning("File system watcher startup ignored. Hot-reloading disabled.")
          {:ok, state}
      end
    end
  end

  @impl true
  def handle_call(:list_commands, _from, state) do
    #Logger.debug("PluginManager received handle_call: :list_commands")
    cmds = Enum.map(state.plugins, fn %{name: name, description: desc} -> %{name: name, description: desc} end)
    Logger.debug("Returning #{length(cmds)} commands.")
    {:reply, cmds, state}
  end

  # --- Handle Casts ---

  @impl true
  def handle_cast(:reload, state) do
    #Logger.info("PluginManager received handle_cast: :reload")
    Logger.info("Received full reload signal. Re-scanning and loading all plugins...")

    # Purge old modules first to ensure clean reload
    Enum.each(state.plugins, fn %{module: mod} ->
      try do
        :code.purge(mod)
        :code.delete(mod)
      rescue
        _ -> :ok
      end
    end)

    new_state = load_plugins()

    new_state = case state[:watcher_pid] do
      nil -> new_state
      watcher_pid -> Map.put(new_state, :watcher_pid, watcher_pid)
    end

    Logger.info("handle_cast(:reload) sending :do_sync_commands cast...")
    GenServer.cast(self(), :do_sync_commands)

    {:noreply, new_state}
  end

  @impl true
  def handle_cast({:plugin_compiled, module_atom, file_path}, state) do
    Logger.info("PluginManager received handle_cast: {:plugin_compiled, #{inspect(module_atom)}, #{file_path}}")
    Logger.info("Received plugin compiled signal for #{inspect(module_atom)}. Attempting to reload specific plugin and sync...")

    case load_single_plugin(module_atom, file_path) do
      nil ->
        Logger.warning("Plugin #{inspect(module_atom)} is no longer valid or loadable after recompile. Removing from state.")
        old_plugins_count = length(state.plugins)
        new_plugins = Enum.filter(state.plugins, fn plugin -> plugin.module != module_atom end)
        new_state = %{state | plugins: new_plugins}
        Logger.debug("State plugins count changed from #{old_plugins_count} to #{length(new_plugins)}.")
        {:noreply, new_state}

      updated_plugin_spec ->
        Logger.info("Successfully reloaded spec for #{inspect(module_atom)} (name: #{updated_plugin_spec.name}).")
        old_plugins_count = length(state.plugins)

        new_plugins =
          Enum.filter(state.plugins, fn plugin -> plugin.module != module_atom end) ++ [updated_plugin_spec]

        new_state = %{state | plugins: new_plugins}
        Logger.debug("State plugins count changed from #{old_plugins_count} to #{length(new_plugins)} after update.")

        guild_id_str = Application.get_env(:nebulixir, :discord_guild_id) |> to_string()
        case Integer.parse(guild_id_str) do
          {guild_id_int, ""} ->
            Logger.info("handle_cast({:plugin_compiled, ...}) triggering single command sync for #{updated_plugin_spec.name}...")
            sync_single_command(updated_plugin_spec, Integer.to_string(guild_id_int))
            {:noreply, new_state}
          :error ->
            Logger.error("Missing or invalid GUILD_ID: #{inspect(guild_id_str)}. Cannot sync updated plugin #{updated_plugin_spec.name}.")
            {:noreply, new_state}
        end
    end
  end

  @impl true
  def handle_cast({:new_plugin_file, file_path}, state) do
    Logger.info("PluginManager received handle_cast: {:new_plugin_file, #{inspect(file_path)}}")
    Logger.info("New plugin file detected: #{file_path}. Attempting to compile and load...")

    Process.sleep(100)

    case compile_and_load_new_plugin(file_path) do
      nil ->
        Logger.warning("Failed to compile or load new plugin from #{file_path}")
        {:noreply, state}

      {module_atom, plugin_spec} ->
        Logger.info("Successfully compiled and loaded new plugin #{inspect(module_atom)} from #{file_path}")

        new_plugins = Enum.filter(state.plugins, fn plugin -> plugin.module != module_atom end) ++ [plugin_spec]
        new_state = %{state | plugins: new_plugins}

        guild_id_str = Application.get_env(:nebulixir, :discord_guild_id) |> to_string()
        case Integer.parse(guild_id_str) do
          {guild_id_int, ""} ->
            Logger.info("Syncing new plugin command: #{plugin_spec.name}")
            sync_single_command(plugin_spec, Integer.to_string(guild_id_int))
            {:noreply, new_state}
          :error ->
            Logger.error("Missing or invalid GUILD_ID: #{inspect(guild_id_str)}. Cannot sync new plugin #{plugin_spec.name}.")
            {:noreply, new_state}
        end
    end
  end

  @impl true
  def handle_cast(:do_sync_commands, state) do
    Logger.info("PluginManager received handle_cast: :do_sync_commands")
    Logger.info("Syncing ALL slash commands with Discord. Total loaded: #{length(state.plugins)}")
    guild_id_str = Application.get_env(:nebulixir, :discord_guild_id) |> to_string()

    case Integer.parse(guild_id_str) do
      {guild_id_int, ""} ->
        guild_id_str = Integer.to_string(guild_id_int)

        _tasks = Enum.map(state.plugins, fn plugin ->
          Task.async(fn ->
            sync_single_command(plugin, guild_id_str)
          end)
        end)

        {:noreply, state}

      :error ->
        Logger.error("Missing or invalid GUILD_ID: #{inspect(guild_id_str)}. Cannot sync commands.")
        {:noreply, state}
    end
  end

  @impl true
  def handle_cast({:dispatch_command, name, interaction, ctx}, state) do
    Logger.info("PluginManager received handle_cast: {:dispatch_command, \"#{name}\", ...}")
    Logger.info("Dispatching command: /#{name}")

    case Enum.find(state.plugins, &(&1.name == name)) do
      nil ->
        available_commands = Enum.map(state.plugins, & &1.name)
        Logger.warning("Unknown command: /#{name}. Available commands: `#{Enum.join(available_commands, ", ")}`")
        try do
          Nostrum.Api.Interaction.create_response(
            interaction.id,
            interaction.token,
            %{
              type: 4,
              data: %{
                content: "Unknown command: `/#{name}`. Available commands: `#{Enum.join(available_commands, ", ")}`",
                flags: 64
              }
            }
          )
        rescue
          err -> Logger.error("Failed to send unknown command response: #{inspect(err)}")
        end

      %{module: mod} ->
        try do
          Logger.debug("Found plugin #{inspect(mod)} for command /#{name}. Calling handle_command.")
          updated_ctx = Map.put(ctx, :plugins, state.plugins)
          mod.handle_command(interaction, updated_ctx)

        rescue
          err ->
            Logger.error("Plugin #{inspect(mod)} crashed during handle_command: #{Exception.message(err)}")
            Logger.error("Stacktrace: #{inspect(__STACKTRACE__)}")
            try do
              Nostrum.Api.Interaction.create_response(
                interaction.id,
                interaction.token,
                %{
                  type: 4,
                  data: %{
                    content: "An internal error occurred while running command `/#{name}`. Please try again later.",
                    flags: 64
                  }
                }
              )
            rescue
              err2 -> Logger.error("Failed to send command crash response: #{inspect(err2)}")
            end
        end
    end

    {:noreply, state}
  end

  # Handle Task completion messages
  def handle_info({_ref, :ok}), do: {:noreply, nil}
  def handle_info({:DOWN, _ref, :process, _pid, :normal}), do: {:noreply, nil}
  def handle_info({:DOWN, _ref, :process, _pid, reason}) do
    Logger.warning("PluginManager Task down with reason: #{inspect(reason)}")
    {:noreply, nil}
  end

  # --- Handle Info ---
  @impl true
  def handle_info({:EXIT, pid, reason}, %{watcher_pid: watcher_pid} = state) when pid == watcher_pid do
    Logger.info("PluginManager received handle_info: {:EXIT, #{inspect(pid)}, #{inspect(reason)}} (from watcher)")
    Logger.error("File system watcher PID #{inspect(pid)} exited: #{inspect(reason)}. Hot-reloading is now disabled.")
    {:noreply, Map.delete(state, :watcher_pid)}
  end

  @impl true
  def handle_info({:file_system, watcher_pid_from_message, event}, %{watcher_pid: watcher_pid_in_state} = state) when watcher_pid_from_message == watcher_pid_in_state do
    Logger.info("PluginManager received handle_info: {:file_system, #{inspect(watcher_pid_from_message)}, #{inspect(event)}} (from watcher) - Watcher PID matches state.")

    case event do
      {:file_event, path, events} ->
        Logger.info("  Received file_event (nested format) for path: #{inspect(path)}, events: #{inspect(events)}")
        abs_path = Path.expand(path)
        abs_plugin_source_dir = Path.expand(@plugin_source_dir)
        Logger.info("  Expanded path: #{inspect(abs_path)}")
        Logger.info("  Plugin source dir: #{inspect(abs_plugin_source_dir)}")

        if String.ends_with?(abs_path, ".ex") and String.starts_with?(abs_path, abs_plugin_source_dir) do
          Logger.info("  Path matches plugin criteria. Checking events...")

          cond do
            # Handle file creation (new plugin)
            Enum.any?(events, fn e -> e == :created end) ->
              Logger.info("handle_info({:file_system, ...}): New plugin file created: #{abs_path}")
              Process.send_after(self(), {:delayed_compile, abs_path}, 500)

            Enum.any?(events, fn e -> e in [:modified, :changed, :close_write] end) ->
              Logger.info("handle_info({:file_system, ...}): Plugin file modified: #{abs_path}")
              if plugin_exists_for_file?(abs_path, state.plugins) do
                compile_and_reload_plugin(abs_path)
              else
                Process.send_after(self(), {:delayed_compile, abs_path}, 200)
              end

            Enum.any?(events, fn e -> e == :deleted end) ->
              Logger.info("handle_info({:file_system, ...}): Plugin file deleted: #{abs_path}")
              GenServer.cast(self(), :reload)

            true ->
              Logger.info("handle_info({:file_system, ...}): Ignoring file event for #{abs_path} (events: #{inspect(events)}). Not a relevant change.")
          end
        else
          Logger.info("handle_info({:file_system, ...}): Ignoring file event for non-plugin source file: #{abs_path}")
        end

      other_event ->
        Logger.info("handle_info({:file_system, ...}): Ignoring other file system event: #{inspect(other_event)}")
    end

    {:noreply, state}
  end

  @impl true
  def handle_info({:file_system, watcher_pid_from_message, event}, state) do
    Logger.warning("PluginManager received handle_info: {:file_system, #{inspect(watcher_pid_from_message)}, #{inspect(event)}} (Watcher PID MISMATCH or no watcher_pid in state: #{inspect(state[:watcher_pid])})")
    {:noreply, state}
  end

  @impl true
  def handle_info({:file_event, watcher_pid_from_message, event}, %{watcher_pid: watcher_pid_in_state} = state) when watcher_pid_from_message == watcher_pid_in_state do
    Logger.info("PluginManager received handle_info: {:file_event, #{inspect(watcher_pid_from_message)}, #{inspect(event)}} (from watcher) - Watcher PID matches state.")

    case event do
      {path, events} when is_binary(path) and is_list(events) ->
        Logger.info("  Matched {:file_event, _, {path, events}} format. Processing...")
        abs_path = Path.expand(path)
        abs_plugin_source_dir = Path.expand(@plugin_source_dir)
        Logger.info("  Expanded path: #{inspect(abs_path)}")
        Logger.info("  Plugin source dir: #{inspect(abs_plugin_source_dir)}")

        if String.ends_with?(abs_path, ".ex") and String.starts_with?(abs_path, abs_plugin_source_dir) do
          Logger.info("  Path matches plugin criteria. Checking events...")
          cond do
            Enum.any?(events, fn e -> e == :created end) ->
              Logger.info("handle_info({:file_event, ...}): New plugin file created: #{abs_path}")
              Process.send_after(self(), {:delayed_compile, abs_path}, 500)

            Enum.any?(events, fn e -> e in [:modified, :changed, :close_write] end) ->
              Logger.info("handle_info({:file_event, ...}): Plugin file modified: #{abs_path}")
              if plugin_exists_for_file?(abs_path, state.plugins) do
                compile_and_reload_plugin(abs_path)
              else
                Process.send_after(self(), {:delayed_compile, abs_path}, 200)
              end

            Enum.any?(events, fn e -> e == :deleted end) ->
              Logger.info("handle_info({:file_event, ...}): Plugin file deleted: #{abs_path}")
              GenServer.cast(self(), :reload)

            true ->
              Logger.info("handle_info({:file_event, ...}): Ignoring file event for #{abs_path} (events: #{inspect(events)}).")
          end
        else
          Logger.info("handle_info({:file_event, ...}): Ignoring file event for non-plugin source file: #{abs_path}")
        end

      :stop ->
        Logger.info("handle_info({:file_event, ...}): Watcher sent stop signal.")
        {:noreply, Map.delete(state, :watcher_pid)}

      other_event_format ->
        Logger.info("handle_info({:file_event, ...}): Received unexpected event format: #{inspect(other_event_format)}")
    end

    {:noreply, state}
  end

  @impl true
  def handle_info({:file_event, watcher_pid_from_message, event}, state) do
    Logger.warning("PluginManager received handle_info: {:file_event, #{inspect(watcher_pid_from_message)}, #{inspect(event)}} (Watcher PID MISMATCH or no watcher_pid in state: #{inspect(state[:watcher_pid])})")
    {:noreply, state}
  end

  @impl true
  def handle_info({:delayed_compile, file_path}, state) do
    Logger.info("Processing delayed compilation for: #{file_path}")
    GenServer.cast(self(), {:new_plugin_file, file_path})
    {:noreply, state}
  end

  @impl true
  def handle_info(_msg, state) do
    #Logger.info("PluginManager received unhandled info: #{inspect(msg)}")
    {:noreply, state}
  end

  @impl true
  def terminate(_reason, %{watcher_pid: watcher_pid} = _state) when is_pid(watcher_pid) do
    Logger.info("PluginManager terminating. Watcher PID #{inspect(watcher_pid)} is linked, will be stopped automatically.")
    :ok
  end

  @impl true
  def terminate(_reason, _state) do
    Logger.info("Terminating PluginManager, no watcher PID to stop.")
    :ok
  end

  ## Internal Helper Functions

  defp load_plugins do
    Logger.info("PluginManager attempting to load ALL plugins from #{@plugin_source_dir}...")

    abs_plugin_source_dir = Path.expand(@plugin_source_dir)

    if File.dir?(abs_plugin_source_dir) do
      case File.ls(abs_plugin_source_dir) do
        {:ok, files} ->
          plugins = Enum.flat_map(files, fn file ->
            full_path = Path.join(abs_plugin_source_dir, file)
            if Path.extname(file) in [".ex", ".exs"] and File.regular?(full_path) do
              case path_to_module_atom(full_path) do
                nil -> []
                module_atom ->
                  #Logger.debug("load_plugins: Mapping file #{full_path} to module: #{inspect(module_atom)}")

                  case Code.compile_file(full_path) do
                    [] ->
                      #Logger.warning("load_plugins: No modules compiled from #{full_path}")
                      []
                    modules ->
                      Logger.debug("load_plugins: Compiled modules from #{full_path}: #{inspect(modules)}")
                      case load_plugin(module_atom) do
                        nil ->
                          Logger.warning("load_plugins: Skipping plugin #{inspect(module_atom)} as load_plugin returned nil.")
                          []
                        plugin_spec ->
                          Logger.debug("load_plugins: Successfully loaded and validated plugin: #{inspect(plugin_spec, max_depth: 2)}")
                          [plugin_spec]
                      end
                  end
              end
            else
              []
            end
          end)
          |> Enum.filter(&(&1 != nil))

          Logger.info("Successfully loaded and validated #{length(plugins)} command plugins.")
          Logger.debug("Loaded plugins: #{inspect(plugins, max_depth: 2)}")
          %{plugins: plugins}

        {:error, reason} ->
          Logger.error("Failed to list plugin directory #{abs_plugin_source_dir}: #{inspect(reason)}")
          %{plugins: []}
      end
    else
      Logger.error("Plugin source directory not found: #{abs_plugin_source_dir}")
      %{plugins: []}
    end
  end

  # FIXED: This is the key fix - recompile from source after purging
  defp load_single_plugin(module_atom, file_path) do
    #Logger.debug("load_single_plugin: Attempting to reload and validate plugin spec for module: #{inspect(module_atom)} from #{file_path}")

    try do
      :code.purge(module_atom)
      :code.delete(module_atom)


      case Code.compile_file(file_path) do
        [] ->
          Logger.error("load_single_plugin: Failed to compile any modules from #{file_path}")
          nil

        modules ->
          Logger.info("load_single_plugin: Successfully recompiled #{file_path}, modules: #{inspect(modules)}")

          case Code.ensure_loaded(module_atom) do
            {:module, mod} ->
              Logger.info("load_single_plugin: Successfully ensured latest code loaded for: #{inspect(mod)}")
              load_plugin(mod)

            {:error, reason} ->
              Logger.error("load_single_plugin: Failed to ensure loaded for #{inspect(module_atom)}: #{inspect(reason)}")
              nil
          end
      end
    rescue
      err ->
        Logger.error("load_single_plugin: Error attempting to reload single plugin #{inspect(module_atom)}: #{Exception.message(err)}")
        Logger.error("Stacktrace: #{inspect(__STACKTRACE__)}")
        nil
    end
  end

  defp load_plugin(mod) do
    Logger.debug("load_plugin: Validating plugin requirements for module: #{inspect(mod)}")

    try do
      if function_exported?(mod, :command_spec, 0) do
        spec = mod.command_spec()
        Logger.debug("load_plugin: Received spec from #{inspect(mod)}: #{inspect(spec)}")

        if is_map(spec) and Map.has_key?(spec, :name) and Map.has_key?(spec, :description) and Map.has_key?(spec, :options) do
          if is_binary(spec.name) and byte_size(spec.name) > 0 do
            if function_exported?(mod, :handle_command, 2) do
              Logger.debug("load_plugin: Module #{inspect(mod)} exports command_spec/0 and handle_command/2. Validated spec name: #{spec.name}.")
              %{name: spec.name, description: spec.description, options: spec.options, module: mod}
            else
              Logger.warning("load_plugin: Skipping plugin #{inspect(mod)}: Does not export handle_command/2.")
              nil
            end
          else
            Logger.warning("load_plugin: Skipping invalid plugin #{inspect(mod)}: command_spec/0 returned invalid name type or empty string. Received: #{inspect(spec)}")
            nil
          end
        else
          Logger.warning("load_plugin: Skipping invalid plugin #{inspect(mod)}: command_spec/0 did not return a valid map with :name, :description, and :options. Received: #{inspect(spec)}")
          nil
        end
      else
        Logger.warning("load_plugin: Skipping plugin #{inspect(mod)}: Does not export command_spec/0.")
        nil
      end
    rescue
      err ->
        Logger.error("load_plugin: Skipping plugin #{inspect(mod)} due to error executing command_spec/0: #{Exception.message(err)}")
        Logger.error("Stacktrace: #{inspect(__STACKTRACE__)}")
        nil
    end
  end

  defp compile_and_reload_plugin(file_path) do
    case path_to_module_atom(file_path) do
      nil ->
        Logger.error("Could not determine module atom for file: #{file_path}")

      module_atom ->
        Logger.info("Compiling and reloading plugin: #{inspect(module_atom)} from #{file_path}")

        case Code.compile_file(file_path) do
          [] ->
            Logger.error("Failed to compile any modules from #{file_path}")

          _modules ->
            Logger.info("Successfully recompiled #{file_path}. Sending plugin_compiled cast.")
            # UPDATED: Pass file_path along with module_atom
            GenServer.cast(self(), {:plugin_compiled, module_atom, file_path})
        end
    end
  end

  defp compile_and_load_new_plugin(file_path) do
    case path_to_module_atom(file_path) do
      nil ->
        Logger.error("Could not determine module atom for new file: #{file_path}")
        nil

      module_atom ->
        Logger.info("Compiling new plugin: #{inspect(module_atom)} from #{file_path}")

        case Code.compile_file(file_path) do
          [] ->
            Logger.error("Failed to compile any modules from #{file_path}")
            nil

          _modules ->
            Logger.info("Successfully compiled new plugin from #{file_path}")
            case load_plugin(module_atom) do
              nil ->
                Logger.warning("New plugin #{inspect(module_atom)} failed validation")
                nil
              plugin_spec ->
                Logger.info("Successfully loaded new plugin: #{plugin_spec.name}")
                {module_atom, plugin_spec}
            end
        end
    end
  end

  defp path_to_module_atom(file_path) do
    try do
      file_base = Path.basename(file_path, Path.extname(file_path))
      module_name_segment =
        file_base
        |> String.split("_")
        |> Enum.map(&String.capitalize/1)
        |> Enum.join()

      Module.concat(@plugin_source_namespace, String.to_atom(module_name_segment))
    rescue
      _ -> nil
    end
  end


  defp plugin_exists_for_file?(file_path, plugins) do
    case path_to_module_atom(file_path) do
      nil -> false
      module_atom ->
        Enum.any?(plugins, fn %{module: mod} -> mod == module_atom end)
    end
  end

  defp sync_single_command(%{module: mod, name: name, description: _desc} = plugin_spec, guild_id_str) do
    Logger.info("sync_single_command: Attempting to sync command /#{name} from module #{inspect(mod)} to guild #{guild_id_str}...")

    try do
      case Code.ensure_loaded(mod) do
        {:module, _} ->
          case Nostrum.Api.ApplicationCommand.create_guild_command(guild_id_str, %{
            name: plugin_spec.name,
            description: plugin_spec.description,
            options: plugin_spec.options
          }) do
            {:ok, _resp} ->
              Logger.info("sync_single_command: Successfully synced /#{plugin_spec.name}.")
            {:error, reason} ->
              Logger.error("sync_single_command: Failed to sync /#{plugin_spec.name}: #{inspect(reason)}")
            _other ->
              Logger.info(":ok")
                #Logger.error("sync_single_command: Unexpected API response syncing /#{plugin_spec.name}: #{inspect(other)}")
          end
        {:error, reason} ->
          Logger.error("sync_single_command: Plugin module #{inspect(mod)} not loaded before sync attempt: #{inspect(reason)}. Cannot sync command /#{plugin_spec.name}.")
      end
    rescue
      err ->
        Logger.error("sync_single_command: Failed API call for #{inspect(mod)} command /#{plugin_spec.name} due to exception: #{Exception.message(err)}")
        Logger.error("Stacktrace: #{inspect(__STACKTRACE__)}")
    end
  end
end
