defmodule Mix.Tasks.Import.FiveEtools do
  @moduledoc """
  Import 5etools JSON data into Neo4j.

  ## Examples

      mix import.5etools
      mix import.5etools --path priv/data/5etools
      mix import.5etools --srd-only
      mix import.5etools --path data/ --srd-only

  ## Options

    * `--path` - Path to directory containing JSON files (default: priv/data/5etools)
    * `--srd-only` - Only import SRD (Systems Reference Document) content
  """
  use Mix.Task

  @shortdoc "Import 5etools JSON data into Neo4j (use: mix import.5etools)"

  @switches [
    path: :string,
    srd_only: :boolean
  ]

  @aliases [
    p: :path,
    s: :srd_only
  ]

  def run(args) do
    {opts, _argv, _errors} = OptionParser.parse(args, switches: @switches, aliases: @aliases)

    path = Keyword.get(opts, :path, "priv/data/5etools")
    srd_only = Keyword.get(opts, :srd_only, false)

    Mix.Task.run("app.start")

    IO.puts("""
    ========================================
    5etools Data Import
    ========================================
    Path: #{path}
    SRD Only: #{srd_only}
    ========================================
    """)

    # Check if files exist, download if needed
    ensure_files_present(path)

    case DndApp.DataImport.import_all(path: path, srd_only: srd_only) do
      :ok ->
        IO.puts("\n✅ Import completed successfully!")

        # Track version after successful import
        track_import_version(path)

        System.halt(0)
      error ->
        IO.puts("\n❌ Import failed: #{inspect(error)}")
        System.halt(1)
    end
  end

  defp track_import_version(path) do
    IO.puts("\n📊 Tracking import version...")

    commit_hash = get_git_commit_hash(path)
    timestamp = DateTime.utc_now() |> DateTime.to_iso8601()

    case DndApp.RiskRegistry.track_version(
      "5etools-data",
      "latest",
      commit_hash,
      %{import_timestamp: timestamp}
    ) do
      {:ok, version_record} ->
        IO.puts("  ✓ Version tracked: #{version_record.version}")
        if commit_hash do
          IO.puts("  ✓ Commit hash: #{String.slice(commit_hash, 0, 8)}...")
        end

        # Check if version changed
        case DndApp.RiskRegistry.get_version_history("5etools-data", 2) do
          {:ok, [current | [previous | _]]} ->
            if current.commit_hash != previous.commit_hash do
              IO.puts("\n⚠️  Version changed!")
              IO.puts("  Previous: #{String.slice(previous.commit_hash || "unknown", 0, 8)}")
              IO.puts("  Current:  #{String.slice(current.commit_hash || "unknown", 0, 8)}")
            else
              IO.puts("  ℹ️  No version change detected")
            end
          _ ->
            IO.puts("  ℹ️  First version tracked")
        end
      error ->
        IO.puts("  ⚠️  Failed to track version: #{inspect(error)}")
    end
  end

  defp get_git_commit_hash(path) do
    # Try to get git commit hash if it's a git repository or submodule
    case System.cmd("git", ["-C", path, "rev-parse", "HEAD"], stderr_to_stdout: true) do
      {hash, 0} -> String.trim(hash)
      _ ->
        # Try as submodule
        case System.cmd("git", ["submodule", "status", path], stderr_to_stdout: true) do
          {output, 0} ->
            # Parse submodule status output: "+abc123... path/to/submodule"
            case Regex.run(~r/^[\+\s]?([a-f0-9]+)/, String.trim(output)) do
              [_, hash] -> hash
              _ -> nil
            end
          _ -> nil
        end
    end
  rescue
    _ -> nil
  end
  end

  defp ensure_files_present(path) do
    required_files = ["races.json", "classes.json", "backgrounds.json"]

    missing_files = Enum.filter(required_files, fn file ->
      file_path = Path.join(path, file)
      not File.exists?(file_path)
    end)

    if length(missing_files) > 0 do
      IO.puts("⚠️  Missing files: #{Enum.join(missing_files, ", ")}")
      IO.puts("Please download 5etools data files to #{path}")
      IO.puts("See #{Path.join(path, "README.md")} for instructions")
      IO.puts("\nContinuing with available files...")
    end
  end
end
