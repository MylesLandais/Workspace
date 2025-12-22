defmodule DndApp.DB.Neo4j do
  @moduledoc """
  Neo4j database operations for D&D character storage.
  Implements idempotent operations using MERGE.
  Uses Boltx driver for Neo4j Bolt protocol.
  """
  require Logger

  @pool_name __MODULE__

  @doc """
  Returns a child specification for the supervisor.
  """
  def child_spec(opts) do
    %{
      id: __MODULE__,
      start: {__MODULE__, :start_link, [opts]},
      type: :worker,
      restart: :transient,
      shutdown: 5000
    }
  end

  def start_link(opts) do
    url = Keyword.get(opts, :url, "bolt://localhost:7687")
    username = Keyword.get(opts, :username, "neo4j")
    password = Keyword.get(opts, :password, "password")

    case Boltx.start_link(url: url, username: username, password: password, name: @pool_name) do
      {:ok, pid} = result ->
        Logger.info("Neo4j connection started successfully: #{inspect(pid)}")
        result
      {:error, reason} = error ->
        Logger.error("Neo4j connection failed: #{inspect(reason)}. Will retry...")
        # Return error to allow supervisor to retry with transient restart policy
        error
    end
  end

  @doc """
  Initialize Neo4j schema with constraints.
  This is idempotent and safe to run multiple times.
  """
  def setup_schema do
    with {:ok, _} <- create_constraints() do
      :ok
    else
      error -> {:error, error}
    end
  end

  defp create_constraints do
    queries = [
      # Unique constraint on character ID
      """
      CREATE CONSTRAINT character_id_unique IF NOT EXISTS
      FOR (c:Character) REQUIRE c.id IS UNIQUE
      """,

      # Unique constraint on race name
      """
      CREATE CONSTRAINT race_name_unique IF NOT EXISTS
      FOR (r:Race) REQUIRE r.name IS UNIQUE
      """,

      # Unique constraint on class name
      """
      CREATE CONSTRAINT class_name_unique IF NOT EXISTS
      FOR (cl:Class) REQUIRE cl.name IS UNIQUE
      """,

      # Unique constraint on background name
      """
      CREATE CONSTRAINT background_name_unique IF NOT EXISTS
      FOR (b:Background) REQUIRE b.name IS UNIQUE
      """,

      # Unique constraint on subrace name
      """
      CREATE CONSTRAINT subrace_name_unique IF NOT EXISTS
      FOR (sr:Subrace) REQUIRE sr.name IS UNIQUE
      """,

      # Unique constraint on feature name
      """
      CREATE CONSTRAINT feature_name_unique IF NOT EXISTS
      FOR (f:Feature) REQUIRE f.name IS UNIQUE
      """,

      # Unique constraint on equipment name
      """
      CREATE CONSTRAINT equipment_name_unique IF NOT EXISTS
      FOR (e:Equipment) REQUIRE e.name IS UNIQUE
      """,

      # Indexes for frequently queried properties
      """
      CREATE INDEX race_source IF NOT EXISTS
      FOR (r:Race) ON (r.source)
      """,

      """
      CREATE INDEX class_source IF NOT EXISTS
      FOR (cl:Class) ON (cl.source)
      """,

      """
      CREATE INDEX background_source IF NOT EXISTS
      FOR (b:Background) ON (b.source)
      """,

      """
      CREATE INDEX feature_level IF NOT EXISTS
      FOR (f:Feature) ON (f.level)
      """,

      # Risk Registry constraints
      """
      CREATE CONSTRAINT dependency_name_unique IF NOT EXISTS
      FOR (d:Dependency) REQUIRE d.name IS UNIQUE
      """,

      """
      CREATE CONSTRAINT risk_id_unique IF NOT EXISTS
      FOR (r:Risk) REQUIRE r.id IS UNIQUE
      """,

      """
      CREATE CONSTRAINT version_id_unique IF NOT EXISTS
      FOR (v:Version) REQUIRE v.id IS UNIQUE
      """,

      """
      CREATE CONSTRAINT trigger_id_unique IF NOT EXISTS
      FOR (t:Trigger) REQUIRE t.id IS UNIQUE
      """,

      """
      CREATE CONSTRAINT constraint_id_unique IF NOT EXISTS
      FOR (c:Constraint) REQUIRE c.id IS UNIQUE
      """,

      """
      CREATE CONSTRAINT component_name_unique IF NOT EXISTS
      FOR (c:Component) REQUIRE c.name IS UNIQUE
      """,

      # Risk Registry indexes
      """
      CREATE INDEX dependency_type_index IF NOT EXISTS
      FOR (d:Dependency) ON (d.type)
      """,

      """
      CREATE INDEX risk_severity_index IF NOT EXISTS
      FOR (r:Risk) ON (r.severity)
      """,

      """
      CREATE INDEX version_timestamp_index IF NOT EXISTS
      FOR (v:Version) ON (v.timestamp)
      """
    ]

    Enum.reduce_while(queries, {:ok, nil}, fn query, _acc ->
      case query(query) do
        {:ok, _result} -> {:cont, {:ok, nil}}
        error -> {:halt, error}
      end
    end)
  end

  @doc """
  Execute a Cypher query with optional parameters.

  Returns {:ok, records} where records is a list of maps with atom keys.
  Each record represents a row from the query result.

  Note: Boltx.query! returns results in a format that may need adjustment
  based on the actual Boltx version. The current implementation assumes
  results are enumerable with key-value pairs that can be converted to maps.
  """
  def query(cypher, params \\ %{}) do
    try do
      result = Boltx.query!(@pool_name, cypher, params)

      # Process results - Boltx may return different formats depending on version
      records = case result do
        # If result is already a list of maps
        list when is_list(list) ->
          Enum.map(list, fn
            # Already a map with string keys - convert to atom keys
            row when is_map(row) ->
              Enum.into(row, %{}, fn
                {key, value} when is_binary(key) -> {String.to_atom(key), value}
                {key, value} -> {key, value}
              end)
            # Tuple format - convert to map
            row when is_tuple(row) ->
              Enum.into(row, %{}, fn {key, value} ->
                key_atom = if is_binary(key), do: String.to_atom(key), else: key
                {key_atom, value}
              end)
            # Other formats - return as-is
            row -> row
          end)
        # Single result (not a list)
        single ->
          [single]
        # Empty result
        _ ->
          []
      end

      {:ok, records}
    rescue
      e ->
        Logger.error("Neo4j query failed: #{inspect(e)}")
        Logger.error("Query: #{String.slice(cypher, 0, 200)}...")
        Logger.error("Params: #{inspect(params)}")
        {:error, e}
    end
  end

  @doc """
  Create or update a character node.
  """
  def upsert_character(character_data) do
    cypher = """
    MERGE (c:Character {id: $id})
    SET c.name = $name,
        c.level = $level,
        c.str = $str,
        c.dex = $dex,
        c.con = $con,
        c.int = $int,
        c.wis = $wis,
        c.cha = $cha,
        c.str_mod = $str_mod,
        c.dex_mod = $dex_mod,
        c.con_mod = $con_mod,
        c.int_mod = $int_mod,
        c.wis_mod = $wis_mod,
        c.cha_mod = $cha_mod,
        c.proficiency_bonus = $proficiency_bonus,
        c.ac = $ac,
        c.max_hp = $max_hp,
        c.current_hp = $current_hp,
        c.race = $race,
        c.class = $class,
        c.background = $background,
        c.skills = $skills,
        c.updated_at = datetime()
    ON CREATE SET c.created_at = datetime()

    WITH c
    MERGE (r:Race {name: $race})
    ON CREATE SET r.created_at = datetime()
    MERGE (c)-[:HAS_RACE]->(r)

    WITH c
    MERGE (cl:Class {name: $class})
    ON CREATE SET cl.created_at = datetime()
    MERGE (c)-[:HAS_CLASS]->(cl)

    WITH c
    MERGE (b:Background {name: $background})
    ON CREATE SET b.created_at = datetime()
    MERGE (c)-[:HAS_BACKGROUND]->(b)

    RETURN c.id as id, c.name as name
    """

    params = %{
      id: character_data.id,
      name: character_data.name,
      level: character_data.level || 1,
      str: character_data.str,
      dex: character_data.dex,
      con: character_data.con,
      int: character_data.int,
      wis: character_data.wis,
      cha: character_data.cha,
      str_mod: character_data.str_mod,
      dex_mod: character_data.dex_mod,
      con_mod: character_data.con_mod,
      int_mod: character_data.int_mod,
      wis_mod: character_data.wis_mod,
      cha_mod: character_data.cha_mod,
      proficiency_bonus: character_data.proficiency_bonus,
      ac: character_data.ac,
      max_hp: character_data.max_hp,
      current_hp: character_data.current_hp || character_data.max_hp,
      race: character_data.race,
      class: character_data.class,
      background: character_data.background,
      skills: Jason.encode!(character_data.skills || [])
    }

    case query(cypher, params) do
      {:ok, result} ->
        Logger.info("Upserted character: #{character_data.name}")
        {:ok, result}
      error ->
        Logger.error("Failed to upsert character #{character_data.name}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Get a character by ID.
  """
  def get_character(id) do
    cypher = """
    MATCH (c:Character {id: $id})
    OPTIONAL MATCH (c)-[:HAS_RACE]->(r:Race)
    OPTIONAL MATCH (c)-[:HAS_CLASS]->(cl:Class)
    OPTIONAL MATCH (c)-[:HAS_BACKGROUND]->(b:Background)
    RETURN c, r.name as race, cl.name as class, b.name as background
    """

    case query(cypher, %{id: id}) do
      {:ok, []} -> {:error, :not_found}
      {:ok, [record | _]} ->
        character = record.c
        skills = case Map.get(character, :skills) do
          nil -> []
          skills_json -> Jason.decode!(skills_json)
        end

        character_data = %{
          id: character.id,
          name: character.name,
          level: character.level,
          str: character.str,
          dex: character.dex,
          con: character.con,
          int: character.int,
          wis: character.wis,
          cha: character.cha,
          str_mod: character.str_mod,
          dex_mod: character.dex_mod,
          con_mod: character.con_mod,
          int_mod: character.int_mod,
          wis_mod: character.wis_mod,
          cha_mod: character.cha_mod,
          proficiency_bonus: character.proficiency_bonus,
          ac: character.ac,
          max_hp: character.max_hp,
          current_hp: character.current_hp,
          race: record.race,
          class: record.class,
          background: record.background,
          skills: skills
        }
        {:ok, character_data}
      error -> error
    end
  end

  @doc """
  List all characters.
  """
  def list_characters do
    cypher = """
    MATCH (c:Character)
    RETURN c.id as id, c.name as name, c.level as level, c.class as class, c.race as race
    ORDER BY c.created_at DESC
    """

    case query(cypher) do
      {:ok, records} ->
        characters = Enum.map(records, fn record ->
          %{
            id: record.id,
            name: record.name,
            level: record.level,
            class: record.class,
            race: record.race
          }
        end)
        {:ok, characters}
      error -> error
    end
  end

  @doc """
  Delete a character by ID.
  """
  def delete_character(id) do
    cypher = """
    MATCH (c:Character {id: $id})
    DETACH DELETE c
    """

    case query(cypher, %{id: id}) do
      {:ok, _} ->
        Logger.info("Deleted character: #{id}")
        :ok
      error ->
        Logger.error("Failed to delete character #{id}: #{inspect(error)}")
        error
    end
  end

  @doc """
  Get races with optional filters for source and legacy content.
  """
  def get_races(opts \\ []) do
    show_legacy = Keyword.get(opts, :show_legacy, false)
    source_filter = Keyword.get(opts, :source, nil)

    where_clauses = []
    where_clauses = if not show_legacy, do: ["NOT r:Legacy" | where_clauses], else: where_clauses
    where_clauses = if source_filter, do: ["r.source = $source" | where_clauses], else: where_clauses

    where_clause = if length(where_clauses) > 0, do: "WHERE " <> Enum.join(where_clauses, " AND "), else: ""

    cypher = """
    MATCH (r:Race)
    #{where_clause}
    OPTIONAL MATCH (r)-[:HAS_SUBRACE]->(sr:Subrace)
    RETURN r, collect(sr) as subraces
    ORDER BY r.name
    """

    params = if source_filter, do: %{source: source_filter}, else: %{}

    case query(cypher, params) do
      {:ok, records} ->
        races = Enum.map(records, fn record ->
          race = record.r
          subraces = record.subraces || []
          %{
            name: race.name,
            source: Map.get(race, :source, "PHB"),
            ability_bonuses: Map.get(race, :ability_bonuses, %{}),
            size: Map.get(race, :size, "Medium"),
            speed: Map.get(race, :speed, 30),
            subraces: Enum.map(subraces, & &1.name)
          }
        end)
        {:ok, races}
      error -> error
    end
  end

  @doc """
  Get classes with optional source filter.
  """
  def get_classes(opts \\ []) do
    source_filter = Keyword.get(opts, :source, nil)

    cypher = """
    MATCH (cl:Class)
    #{if source_filter, do: "WHERE cl.source = $source", else: ""}
    OPTIONAL MATCH (cl)-[:HAS_SUBCLASS]->(sc:Subclass)
    RETURN cl, collect(sc) as subclasses
    ORDER BY cl.name
    """

    params = if source_filter, do: %{source: source_filter}, else: %{}

    case query(cypher, params) do
      {:ok, records} ->
        classes = Enum.map(records, fn record ->
          class = record.cl
          %{
            name: class.name,
            source: Map.get(class, :source, "PHB"),
            hit_die: Map.get(class, :hit_die, 8),
            primary_ability: Map.get(class, :primary_ability, :str)
          }
        end)
        {:ok, classes}
      error -> error
    end
  end

  @doc """
  Get backgrounds with optional source filter.
  """
  def get_backgrounds(opts \\ []) do
    source_filter = Keyword.get(opts, :source, nil)

    cypher = """
    MATCH (b:Background)
    #{if source_filter, do: "WHERE b.source = $source", else: ""}
    RETURN b
    ORDER BY b.name
    """

    params = if source_filter, do: %{source: source_filter}, else: %{}

    case query(cypher, params) do
      {:ok, records} ->
        backgrounds = Enum.map(records, fn record ->
          bg = record.b
          %{
            name: bg.name,
            source: Map.get(bg, :source, "PHB"),
            description: Map.get(bg, :description, "")
          }
        end)
        {:ok, backgrounds}
      error -> error
    end
  end

  @doc """
  Get ability bonuses for a race.
  """
  def get_race_bonuses(race_name) do
    cypher = """
    MATCH (r:Race {name: $race_name})
    OPTIONAL MATCH (r)-[:PROVIDES_BONUS]->(ab)
    RETURN r, collect(ab) as bonuses
    """

    case query(cypher, %{race_name: race_name}) do
      {:ok, []} -> {:ok, %{}}
      {:ok, [record | _]} ->
        race = record.r
        bonuses = Map.get(race, :ability_bonuses, %{})
        {:ok, bonuses}
      error -> error
    end
  end

  @doc """
  Get subraces for a race.
  """
  def get_subraces(race_name) do
    cypher = """
    MATCH (r:Race {name: $race_name})-[:HAS_SUBRACE]->(sr:Subrace)
    RETURN sr
    ORDER BY sr.name
    """

    case query(cypher, %{race_name: race_name}) do
      {:ok, records} ->
        subraces = Enum.map(records, fn record ->
          sr = record.sr
          %{
            name: sr.name,
            source: Map.get(sr, :source, "PHB"),
            ability_bonuses: Map.get(sr, :ability_bonuses, %{})
          }
        end)
        {:ok, subraces}
      error -> error
    end
  end

  @doc """
  Save a character draft (incomplete character).
  """
  def save_character_draft(draft_data) do
    cypher = """
    MERGE (d:Draft {id: $id})
    SET d.data = $data,
        d.updated_at = datetime()
    ON CREATE SET d.created_at = datetime()
    RETURN d.id as id
    """

    params = %{
      id: draft_data.id,
      data: Jason.encode!(draft_data)
    }

    case query(cypher, params) do
      {:ok, _} -> :ok
      error -> error
    end
  end

  @doc """
  Load a character draft by ID.
  """
  def load_character_draft(id) do
    cypher = """
    MATCH (d:Draft {id: $id})
    RETURN d.data as data
    """

    case query(cypher, %{id: id}) do
      {:ok, []} -> {:error, :not_found}
      {:ok, [record | _]} ->
        case Jason.decode(record.data) do
          {:ok, data} -> {:ok, data}
          error -> error
        end
      error -> error
    end
  end
end
