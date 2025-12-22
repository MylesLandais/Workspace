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
        System.halt(0)
      error ->
        IO.puts("\n❌ Import failed: #{inspect(error)}")
        System.halt(1)
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
