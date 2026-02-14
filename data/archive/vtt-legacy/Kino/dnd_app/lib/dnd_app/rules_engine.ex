defmodule DndApp.RulesEngine do
  @moduledoc """
  Rules engine for applying D&D 5e game rules.
  Queries Neo4j for rule data and applies calculations.
  """
  require Logger
  alias DndApp.DB.Neo4j
  alias DndApp.Characters

  @doc """
  Apply racial bonuses to ability scores.
  Queries Neo4j for the race's ability bonuses.
  """
  def apply_race_bonuses(base_scores, race_name) when is_map(base_scores) do
    case Neo4j.get_race_bonuses(race_name) do
      {:ok, bonuses} when is_map(bonuses) ->
        Enum.reduce(bonuses, base_scores, fn {ability, bonus}, acc ->
          current = Map.get(acc, ability, 10)
          Map.put(acc, ability, current + bonus)
        end)
      {:ok, _} ->
        base_scores
      {:error, _} ->
        # Fallback to Characters context if Neo4j fails
        Characters.apply_race_bonuses(base_scores, race_name)
    end
  end

  def apply_race_bonuses(base_scores, _race_name), do: base_scores

  @doc """
  Get class features at a specific level.
  """
  def get_class_features(class_name, level) do
    cypher = """
    MATCH (cl:Class {name: $class_name})-[:GRANTS_FEATURE {at_level: $level}]->(f:Feature)
    RETURN f
    ORDER BY f.name
    """

    case Neo4j.query(cypher, %{class_name: class_name, level: level}) do
      {:ok, records} ->
        features = Enum.map(records, fn record ->
          f = record.f
          %{
            name: f.name,
            level: f.level,
            entries: case Map.get(f, :entries) do
              nil -> []
              entries_json -> Jason.decode!(entries_json)
            end
          }
        end)
        {:ok, features}
      error -> error
    end
  end

  @doc """
  Validate prerequisites for a class or race.
  """
  def validate_prerequisites(character_data) do
    # For now, basic validation
    # Can be expanded to check ability score requirements, etc.
    {:ok, []}
  end

  @doc """
  Calculate derived stats (HP, AC, proficiency bonus).
  """
  def calculate_derived_stats(character_data) do
    level = Map.get(character_data, :level, 1)
    class = Map.get(character_data, :class)
    con_mod = Map.get(character_data, :con_mod, 0)
    dex_mod = Map.get(character_data, :dex_mod, 0)

    hp = if class do
      Characters.calculate_starting_hp(class, con_mod, level)
    else
      nil
    end

    ac = Characters.calculate_ac(dex_mod)
    prof_bonus = Characters.proficiency_bonus(level)

    %{
      hp: hp,
      ac: ac,
      proficiency_bonus: prof_bonus
    }
  end
end
