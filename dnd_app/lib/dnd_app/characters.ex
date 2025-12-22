defmodule DndApp.Characters do
  @moduledoc """
  Context for managing D&D 5e characters.
  Handles character creation, stat calculation, and business logic.
  """
  alias DndApp.Dice
  alias DndApp.DB.Neo4j
  require Logger

  # Fallback data if Neo4j is unavailable
  @fallback_races [
    %{name: "Human", ability_bonuses: %{str: 1, dex: 1, con: 1, int: 1, wis: 1, cha: 1}},
    %{name: "Elf", ability_bonuses: %{dex: 2, wis: 1}},
    %{name: "Dwarf", ability_bonuses: %{con: 2, str: 1}},
    %{name: "Halfling", ability_bonuses: %{dex: 2, cha: 1}},
    %{name: "Dragonborn", ability_bonuses: %{str: 2, cha: 1}},
    %{name: "Gnome", ability_bonuses: %{int: 2, con: 1}},
    %{name: "Half-Elf", ability_bonuses: %{cha: 2, str: 1, dex: 1}},
    %{name: "Half-Orc", ability_bonuses: %{str: 2, con: 1}},
    %{name: "Tiefling", ability_bonuses: %{cha: 2, int: 1}}
  ]

  @fallback_classes [
    %{name: "Barbarian", hit_die: 12, primary_ability: :str},
    %{name: "Bard", hit_die: 8, primary_ability: :cha},
    %{name: "Cleric", hit_die: 8, primary_ability: :wis},
    %{name: "Druid", hit_die: 8, primary_ability: :wis},
    %{name: "Fighter", hit_die: 10, primary_ability: :str},
    %{name: "Monk", hit_die: 8, primary_ability: :dex},
    %{name: "Paladin", hit_die: 10, primary_ability: :str},
    %{name: "Ranger", hit_die: 10, primary_ability: :dex},
    %{name: "Rogue", hit_die: 8, primary_ability: :dex},
    %{name: "Sorcerer", hit_die: 6, primary_ability: :cha},
    %{name: "Warlock", hit_die: 8, primary_ability: :cha},
    %{name: "Wizard", hit_die: 6, primary_ability: :int}
  ]

  @fallback_backgrounds [
    "Acolyte", "Criminal", "Folk Hero", "Noble", "Sage",
    "Soldier", "Hermit", "Entertainer", "Guild Artisan", "Outlander"
  ]

  # D&D 5e Skills
  @skills [
    "Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception",
    "History", "Insight", "Intimidation", "Investigation", "Medicine",
    "Nature", "Perception", "Performance", "Persuasion", "Religion",
    "Sleight of Hand", "Stealth", "Survival"
  ]

  @doc """
  Get races from Neo4j, with fallback to hardcoded data.
  """
  def races(opts \\ []) do
    case Neo4j.get_races(opts) do
      {:ok, races} when length(races) > 0 -> races
      _ -> @fallback_races
    end
  end

  @doc """
  Get classes from Neo4j, with fallback to hardcoded data.
  """
  def classes(opts \\ []) do
    case Neo4j.get_classes(opts) do
      {:ok, classes} when length(classes) > 0 -> classes
      _ -> @fallback_classes
    end
  end

  @doc """
  Get backgrounds from Neo4j, with fallback to hardcoded data.
  """
  def backgrounds(opts \\ []) do
    case Neo4j.get_backgrounds(opts) do
      {:ok, backgrounds} when length(backgrounds) > 0 ->
        Enum.map(backgrounds, & &1.name)
      _ -> @fallback_backgrounds
    end
  end

  def skills, do: @skills

  @doc """
  Generate ability scores using 4d6 drop lowest method.
  Returns 6 ability score values.
  """
  def generate_ability_scores do
    Dice.roll_ability_scores()
  end

  @doc """
  Calculate ability modifier from ability score.
  Formula: (score - 10) / 2, rounded down.
  """
  def ability_modifier(score) when is_integer(score) do
    floor_div((score - 10) / 2)
  end

  @doc """
  Calculate proficiency bonus based on level.
  Formula: 2 + (level - 1) / 4, rounded up.
  """
  def proficiency_bonus(level) when is_integer(level) and level >= 1 do
    ceil_div(2 + (level - 1) / 4)
  end

  @doc """
  Apply race ability score bonuses to base scores.
  Uses rules engine for Neo4j queries, with fallback.
  """
  def apply_race_bonuses(base_scores, race_name) do
    alias DndApp.RulesEngine
    RulesEngine.apply_race_bonuses(base_scores, race_name)
  end

  @doc """
  Calculate starting HP based on class and constitution modifier.
  Level 1: max hit die + CON modifier
  """
  def calculate_starting_hp(class_name, con_mod, level \\ 1) do
    class = Enum.find(@classes, &(&1.name == class_name))
    hit_die = if class, do: class.hit_die, else: 8

    if level == 1 do
      hit_die + con_mod
    else
      # For higher levels, average roll + CON mod per level
      avg_roll = (hit_die / 2) |> ceil_div()
      (hit_die + con_mod) + (avg_roll + con_mod) * (level - 1)
    end
  end

  @doc """
  Calculate Armor Class.
  Base AC: 10 + DEX modifier (unarmored)
  """
  def calculate_ac(dex_mod, armor \\ nil) do
    case armor do
      nil -> 10 + dex_mod
      _ -> 10 + dex_mod  # Simplified for MVP
    end
  end

  @doc """
  Get race by name.
  """
  def get_race(name) do
    case races() do
      races when is_list(races) -> Enum.find(races, &(&1.name == name))
      _ -> Enum.find(@fallback_races, &(&1.name == name))
    end
  end

  @doc """
  Get class by name.
  """
  def get_class(name) do
    case classes() do
      classes when is_list(classes) -> Enum.find(classes, &(&1.name == name))
      _ -> Enum.find(@fallback_classes, &(&1.name == name))
    end
  end

  @doc """
  Create a new character with the given attributes.
  """
  def create_character(attrs) do
    # Generate ID
    id = UUID.uuid4()

    # Extract ability scores
    base_scores = %{
      str: attrs[:str] || 10,
      dex: attrs[:dex] || 10,
      con: attrs[:con] || 10,
      int: attrs[:int] || 10,
      wis: attrs[:wis] || 10,
      cha: attrs[:cha] || 10
    }

    # Apply race bonuses
    final_scores = apply_race_bonuses(base_scores, attrs[:race])

    # Calculate modifiers
    str_mod = ability_modifier(final_scores.str)
    dex_mod = ability_modifier(final_scores.dex)
    con_mod = ability_modifier(final_scores.con)
    int_mod = ability_modifier(final_scores.int)
    wis_mod = ability_modifier(final_scores.wis)
    cha_mod = ability_modifier(final_scores.cha)

    # Calculate derived stats
    level = attrs[:level] || 1
    prof_bonus = proficiency_bonus(level)
    max_hp = calculate_starting_hp(attrs[:class], con_mod, level)
    ac = calculate_ac(dex_mod)

    character_data = %{
      id: id,
      name: attrs[:name] || "Unnamed Character",
      level: level,
      str: final_scores.str,
      dex: final_scores.dex,
      con: final_scores.con,
      int: final_scores.int,
      wis: final_scores.wis,
      cha: final_scores.cha,
      str_mod: str_mod,
      dex_mod: dex_mod,
      con_mod: con_mod,
      int_mod: int_mod,
      wis_mod: wis_mod,
      cha_mod: cha_mod,
      proficiency_bonus: prof_bonus,
      ac: ac,
      max_hp: max_hp,
      current_hp: max_hp,
      race: attrs[:race] || "Human",
      class: attrs[:class] || "Fighter",
      background: attrs[:background] || "Folk Hero",
      skills: attrs[:skills] || []
    }

    # Save to Neo4j
    case Neo4j.upsert_character(character_data) do
      {:ok, _} -> {:ok, character_data}
      error -> error
    end
  end

  @doc """
  Get a character by ID.
  """
  def get_character(id) do
    Neo4j.get_character(id)
  end

  @doc """
  List all characters.
  """
  def list_characters do
    Neo4j.list_characters()
  end

  @doc """
  Delete a character by ID.
  """
  def delete_character(id) do
    Neo4j.delete_character(id)
  end

  # Helper function for floor division
  defp floor_div(x) when x >= 0, do: trunc(x)
  defp floor_div(x), do: trunc(x) - (if rem(trunc(x), 1) != 0, do: 1, else: 0)

  # Helper function for ceiling
  defp ceil_div(x) do
    t = trunc(x)
    if x > t, do: t + 1, else: t
  end
end
