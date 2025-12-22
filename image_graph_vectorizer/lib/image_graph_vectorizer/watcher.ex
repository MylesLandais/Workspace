defmodule ImageGraphVectorizer.Watcher do
  @moduledoc """
  File system watcher with hot-reload capabilities.
  Handles initial batch load and real-time file changes.
  """
  use GenServer
  require Logger
  alias ImageGraphVectorizer.Processor

  def start_link(_args) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  @impl true
  def init(_) do
    watch_dir = Application.get_env(:image_graph_vectorizer, :watch_dir)
    
    # Validate watch directory exists
    unless File.dir?(watch_dir) do
      Logger.error("Watch directory does not exist: #{watch_dir}")
      {:stop, :invalid_watch_dir}
    else
      # Start file system watcher
      {:ok, watcher_pid} = FileSystem.start_link(dirs: [watch_dir])
      FileSystem.subscribe(watcher_pid)

      # Schedule initial batch scan (async to not block init)
      Process.send_after(self(), :initial_scan, 100)

      {:ok, %{watch_dir: watch_dir, watcher_pid: watcher_pid}}
    end
  end

  @impl true
  def handle_info(:initial_scan, state) do
    Logger.info("Starting initial batch scan of #{state.watch_dir}...")
    
    start_time = System.monotonic_time(:millisecond)
    
    images = discover_images(state.watch_dir)
    Logger.info("Found #{length(images)} images to process")
    
    # Process in parallel using Task.Supervisor
    images
    |> Task.async_stream(
         &Processor.process_file/1,
         max_concurrency: System.schedulers_online() * 2,
         timeout: :infinity
       )
    |> Stream.run()
    
    elapsed = System.monotonic_time(:millisecond) - start_time
    Logger.info("Initial scan complete in #{elapsed}ms. Watching for changes...")
    
    {:noreply, state}
  end

  @impl true
  def handle_info({:file_event, _watcher_pid, {path, events}}, state) do
    cond do
      :deleted in events ->
        handle_deletion(path)
        
      valid_image?(path) and (:created in events or :modified in events) ->
        # Small delay to ensure file is fully written
        Process.sleep(100)
        Processor.process_file(path)
        
      true ->
        :ok
    end

    {:noreply, state}
  end

  @impl true
  def handle_info({:file_event, _watcher_pid, :stop}, state) do
    Logger.warn("File watcher stopped unexpectedly")
    {:noreply, state}
  end

  # Private Functions

  defp discover_images(dir) do
    extensions = Application.get_env(:image_graph_vectorizer, :image_extensions)
    pattern = "*{#{Enum.join(extensions, ",")}}"
    
    Path.join([dir, "**", pattern])
    |> Path.wildcard()
    |> Enum.filter(&File.regular?/1)
  end

  defp valid_image?(path) do
    extensions = Application.get_env(:image_graph_vectorizer, :image_extensions)
    ext = Path.extname(path) |> String.downcase()
    ext in extensions
  end

  defp handle_deletion(path) do
    Logger.info("Handling deletion: #{path}")
    ImageGraphVectorizer.DB.Neo4j.delete_image(path)
  end
end