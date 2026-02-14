defmodule DndApp.DataCase do
  @moduledoc """
  This module defines the test case to be used by
  tests that require setting up data.

  Since we're using Neo4j, we'll set up test data helpers here.
  Provides SRD seed data and test character creation helpers.
  """

  use ExUnit.CaseTemplate

  using do
    quote do
      alias DndApp.DataCase
      alias DndApp.DB.Neo4j
      alias DndApp.Characters
    end
  end

  setup tags do
    # Clean up test data before each test
    if tags[:async] do
      # For async tests, we might want to use a separate test database
      :ok
    else
      # For sync tests, clean up after
      on_exit(fn ->
        cleanup_test_data()
      end)
    end

    :ok
  end

  @doc """
  Get SRD-only race data for testing.
  """
  def srd_races do
    [
      %{
        name: "Human",
        source: "PHB",
        ability_bonuses: %{str: 1, dex: 1, con: 1, int: 1, wis: 1, cha: 1},
        size: "Medium",
        speed: 30,
        subraces: []
      },
      %{
        name: "Elf",
        source: "PHB",
        ability_bonuses: %{dex: 2},
        size: "Medium",
        speed: 30,
        subraces: [
          %{name: "High Elf", source: "PHB", ability_bonuses: %{int: 1}},
          %{name: "Wood Elf", source: "PHB", ability_bonuses: %{wis: 1}}
        ]
      },
      %{
        name: "Dwarf",
        source: "PHB",
        ability_bonuses: %{con: 2},
        size: "Medium",
        speed: 25,
        subraces: [
          %{name: "Hill Dwarf", source: "PHB", ability_bonuses: %{wis: 1}},
          %{name: "Mountain Dwarf", source: "PHB", ability_bonuses: %{str: 2}}
        ]
      },
      %{
        name: "Halfling",
        source: "PHB",
        ability_bonuses: %{dex: 2},
        size: "Small",
        speed: 25,
        subraces: [
          %{name: "Lightfoot", source: "PHB", ability_bonuses: %{cha: 1}},
          %{name: "Stout", source: "PHB", ability_bonuses: %{con: 1}}
        ]
      }
    ]
  end

  @doc """
  Get SRD-only class data for testing.
  """
  def srd_classes do
    [
      %{name: "Fighter", source: "PHB", hit_die: 10, primary_ability: "str"},
      %{name: "Wizard", source: "PHB", hit_die: 6, primary_ability: "int"},
      %{name: "Cleric", source: "PHB", hit_die: 8, primary_ability: "wis"},
      %{name: "Rogue", source: "PHB", hit_die: 8, primary_ability: "dex"},
      %{name: "Ranger", source: "PHB", hit_die: 10, primary_ability: "dex"}
    ]
  end

  @doc """
  Get SRD-only background data for testing.
  """
  def srd_backgrounds do
    [
      %{name: "Acolyte", source: "PHB"},
      %{name: "Criminal", source: "PHB"},
      %{name: "Folk Hero", source: "PHB"},
      %{name: "Noble", source: "PHB"},
      %{name: "Sage", source: "PHB"},
      %{name: "Soldier", source: "PHB"}
    ]
  end

  @doc """
  Seed SRD race data into Neo4j for testing.
  """
  def seed_srd_races do
    races = srd_races()

    Enum.each(races, fn race ->
      cypher = """
      MERGE (r:Race {name: $name, source: $source})
      SET r.size = $size,
          r.speed = $speed,
          r.ability_bonuses = $ability_bonuses,
          r.updated_at = datetime()
      ON CREATE SET r.created_at = datetime()
      """

      params = %{
        name: race.name,
        source: race.source,
        size: race.size,
        speed: race.speed,
        ability_bonuses: Jason.encode!(race.ability_bonuses)
      }

      case Neo4j.query(cypher, params) do
        {:ok, _} ->
          # Create subraces if any
          Enum.each(race.subraces, fn subrace ->
            subrace_cypher = """
            MATCH (r:Race {name: $race_name})
            MERGE (sr:Subrace {name: $name, source: $source})
            SET sr.ability_bonuses = $ability_bonuses
            MERGE (r)-[:HAS_SUBRACE]->(sr)
            """

            subrace_params = %{
              race_name: race.name,
              name: subrace.name,
              source: subrace.source,
              ability_bonuses: Jason.encode!(subrace.ability_bonuses)
            }

            Neo4j.query(subrace_cypher, subrace_params)
          end)
        error ->
          error
      end
    end)

    :ok
  end

  @doc """
  Seed SRD class data into Neo4j for testing.
  """
  def seed_srd_classes do
    classes = srd_classes()

    Enum.each(classes, fn class ->
      cypher = """
      MERGE (cl:Class {name: $name, source: $source})
      SET cl.hit_die = $hit_die,
          cl.primary_ability = $primary_ability,
          cl.updated_at = datetime()
      ON CREATE SET cl.created_at = datetime()
      """

      params = %{
        name: class.name,
        source: class.source,
        hit_die: class.hit_die,
        primary_ability: class.primary_ability
      }

      Neo4j.query(cypher, params)
    end)

    :ok
  end

  @doc """
  Seed SRD background data into Neo4j for testing.
  """
  def seed_srd_backgrounds do
    backgrounds = srd_backgrounds()

    Enum.each(backgrounds, fn bg ->
      cypher = """
      MERGE (b:Background {name: $name, source: $source})
      SET b.updated_at = datetime()
      ON CREATE SET b.created_at = datetime()
      """

      params = %{
        name: bg.name,
        source: bg.source
      }

      Neo4j.query(cypher, params)
    end)

    :ok
  end

  @doc """
  Seed all SRD data (races, classes, backgrounds).
  """
  def seed_all_srd_data do
    seed_srd_races()
    seed_srd_classes()
    seed_srd_backgrounds()
    :ok
  end

  @doc """
  Create a test character with default attributes.
  """
  def create_test_character(attrs \\ %{}) do
    default_attrs = %{
      name: "Test Character",
      race: "Human",
      class: "Fighter",
      background: "Folk Hero",
      level: 1,
      str: 15,
      dex: 14,
      con: 13,
      int: 12,
      wis: 10,
      cha: 8
    }

    attrs = Map.merge(default_attrs, attrs)
    Characters.create_character(attrs)
  end

  @doc """
  Create a test character draft.
  """
  def create_test_draft(attrs \\ %{}) do
    draft_id = UUID.uuid4()
    default_draft = %{
      id: draft_id,
      name: "",
      class: nil,
      background: nil,
      race: nil,
      ability_method: :point_buy,
      base_scores: %{str: 8, dex: 8, con: 8, int: 8, wis: 8, cha: 8}
    }

    draft_data = Map.merge(default_draft, attrs)
    Neo4j.save_character_draft(draft_data)
    {:ok, draft_data}
  end

  defp cleanup_test_data do
    # Clean up test characters and drafts
    # This is a placeholder - actual implementation depends on test strategy
    # In a real implementation, you might:
    # 1. Tag test data with a test identifier
    # 2. Delete all test-tagged data
    # 3. Or use a separate test database
    :ok
  end
end
