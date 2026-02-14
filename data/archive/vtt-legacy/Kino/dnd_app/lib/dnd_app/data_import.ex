defmodule DndApp.DataImport do
  @moduledoc """
  Context for importing 5etools JSON data into Neo4j.
  Supports SRD filtering and idempotent operations.
  """
  require Logger
  alias DndApp.DataImport.Parser
  alias DndApp.DB.Neo4j

  @srd_sources ["PHB", "SRD", "Basic Rules"]

  @doc """
  Import all data files (races, classes, backgrounds).
  """
  def import_all(opts \\ []) do
    srd_only = Keyword.get(opts, :srd_only, false)
    path = Keyword.get(opts, :path, "priv/data/5etools")

    Logger.info("Starting data import (SRD only: #{srd_only})")

    with {:ok, _} <- import_races(path, srd_only: srd_only),
         {:ok, _} <- import_classes(path, srd_only: srd_only),
         {:ok, _} <- import_backgrounds(path, srd_only: srd_only) do
      Logger.info("Data import completed successfully")
      :ok
    else
      error ->
        Logger.error("Data import failed: #{inspect(error)}")
        error
    end
  end

  @doc """
  Import races from races.json.
  """
  def import_races(path, opts \\ []) do
    srd_only = Keyword.get(opts, :srd_only, false)
    file_path = Path.join(path, "races.json")

    case File.read(file_path) do
      {:ok, content} ->
        races = Parser.parse_races(content)
        filtered_races = if srd_only, do: filter_srd_only(races), else: races

        Logger.info("Importing #{length(filtered_races)} races...")

        Enum.each(filtered_races, fn race ->
          import_race(race)
        end)

        {:ok, length(filtered_races)}
      {:error, reason} ->
        Logger.error("Failed to read races.json: #{inspect(reason)}")
        {:error, reason}
    end
  end

  defp import_race(race) do
    labels = if race.is_legacy, do: ["Race", "Legacy"], else: ["Race"]

    cypher = """
    MERGE (r:Race {name: $name, source: $source})
    SET r.size = $size,
        r.speed = $speed,
        r.ability_bonuses = $ability_bonuses,
        r.entries = $entries,
        r.updated_at = datetime()
    ON CREATE SET r.created_at = datetime()
    REMOVE r:Legacy
    #{if race.is_legacy, do: "SET r:Legacy", else: ""}
    WITH r
    UNWIND $subraces AS subrace_data
    MERGE (sr:Subrace {name: subrace_data.name, source: subrace_data.source})
    SET sr.ability_bonuses = subrace_data.ability_bonuses,
        sr.entries = subrace_data.entries
    MERGE (r)-[:HAS_SUBRACE]->(sr)
    """

    subraces_data = Enum.map(race.subraces, fn sr ->
      %{
        name: sr.name,
        source: sr.source,
        ability_bonuses: sr.ability,
        entries: Jason.encode!(sr.entries)
      }
    end)

    params = %{
      name: race.name,
      source: race.source,
      size: race.size,
      speed: race.speed,
      ability_bonuses: Jason.encode!(race.ability),
      entries: Jason.encode!(race.entries),
      subraces: subraces_data
    }

    case Neo4j.query(cypher, params) do
      {:ok, _} -> :ok
      error ->
        Logger.warn("Failed to import race #{race.name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Import classes from classes.json.
  """
  def import_classes(path, opts \\ []) do
    srd_only = Keyword.get(opts, :srd_only, false)
    file_path = Path.join(path, "classes.json")

    case File.read(file_path) do
      {:ok, content} ->
        classes = Parser.parse_classes(content)
        filtered_classes = if srd_only, do: filter_srd_only(classes), else: classes

        Logger.info("Importing #{length(filtered_classes)} classes...")

        Enum.each(filtered_classes, fn class ->
          import_class(class)
        end)

        {:ok, length(filtered_classes)}
      {:error, reason} ->
        Logger.error("Failed to read classes.json: #{inspect(reason)}")
        {:error, reason}
    end
  end

  defp import_class(class) do
    cypher = """
    MERGE (cl:Class {name: $name, source: $source})
    SET cl.hit_die = $hit_die,
        cl.primary_ability = $primary_ability,
        cl.updated_at = datetime()
    ON CREATE SET cl.created_at = datetime()
    WITH cl
    UNWIND $subclasses AS subclass_data
    MERGE (sc:Subclass {name: subclass_data.name, source: subclass_data.source})
    SET sc.short_name = subclass_data.short_name
    MERGE (cl)-[:HAS_SUBCLASS]->(sc)
    WITH cl
    UNWIND $features AS feature_data
    MERGE (f:Feature {name: feature_data.name})
    SET f.level = feature_data.level,
        f.entries = feature_data.entries
    MERGE (cl)-[:GRANTS_FEATURE {at_level: feature_data.level}]->(f)
    """

    subclasses_data = Enum.map(class.subclasses, fn sc ->
      %{
        name: sc.name,
        source: sc.source,
        short_name: sc.short_name || sc.name
      }
    end)

    features_data = Enum.map(class.features, fn f ->
      %{
        name: f.name,
        level: f.level,
        entries: Jason.encode!(f.entries)
      }
    end)

    params = %{
      name: class.name,
      source: class.source,
      hit_die: class.hit_die,
      primary_ability: to_string(class.primary_ability),
      subclasses: subclasses_data,
      features: features_data
    }

    case Neo4j.query(cypher, params) do
      {:ok, _} -> :ok
      error ->
        Logger.warn("Failed to import class #{class.name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Import backgrounds from backgrounds.json.
  """
  def import_backgrounds(path, opts \\ []) do
    srd_only = Keyword.get(opts, :srd_only, false)
    file_path = Path.join(path, "backgrounds.json")

    case File.read(file_path) do
      {:ok, content} ->
        backgrounds = Parser.parse_backgrounds(content)
        filtered_backgrounds = if srd_only, do: filter_srd_only(backgrounds), else: backgrounds

        Logger.info("Importing #{length(filtered_backgrounds)} backgrounds...")

        Enum.each(filtered_backgrounds, fn bg ->
          import_background(bg)
        end)

        {:ok, length(filtered_backgrounds)}
      {:error, reason} ->
        Logger.error("Failed to read backgrounds.json: #{inspect(reason)}")
        {:error, reason}
    end
  end

  defp import_background(bg) do
    cypher = """
    MERGE (b:Background {name: $name, source: $source})
    SET b.entries = $entries,
        b.skill_proficiencies = $skill_proficiencies,
        b.starting_equipment = $starting_equipment,
        b.updated_at = datetime()
    ON CREATE SET b.created_at = datetime()
    """

    params = %{
      name: bg.name,
      source: bg.source,
      entries: Jason.encode!(bg.entries),
      skill_proficiencies: Jason.encode!(bg.skill_proficiencies),
      starting_equipment: Jason.encode!(bg.starting_equipment)
    }

    case Neo4j.query(cypher, params) do
      {:ok, _} -> :ok
      error ->
        Logger.warn("Failed to import background #{bg.name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Filter data to SRD-only content.
  """
  def filter_srd_only(data) when is_list(data) do
    Enum.filter(data, fn item ->
      source = Map.get(item, :source, "")
      source in @srd_sources
    end)
  end

  def filter_srd_only(_), do: []
end
