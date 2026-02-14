defmodule DndApp.DataImport.Parser do
  @moduledoc """
  Parser for 5etools JSON data files.
  Handles nested structures and extracts game content data.
  """

  @doc """
  Parse races.json file content.
  """
  def parse_races(json_content) do
    case Jason.decode(json_content) do
      {:ok, %{"race" => races}} ->
        Enum.map(races, &parse_race/1)
      {:ok, races} when is_list(races) ->
        Enum.map(races, &parse_race/1)
      error ->
        error
    end
  end

  defp parse_race(race_data) do
    %{
      name: get_string(race_data, "name"),
      source: normalize_source(get_string(race_data, "source")),
      ability: parse_ability_bonuses(race_data),
      size: get_string(race_data, "size", ["M", "Medium"]),
      speed: parse_speed(race_data),
      entries: get_list(race_data, "entries", []),
      subraces: parse_subraces(get_list(race_data, "subraces", [])),
      is_legacy: Map.get(race_data, "isLegacy", false)
    }
  end

  defp parse_subraces(subraces_data) do
    Enum.map(subraces_data, fn subrace ->
      %{
        name: get_string(subrace, "name"),
        source: normalize_source(get_string(subrace, "source")),
        ability: parse_ability_bonuses(subrace),
        entries: get_list(subrace, "entries", [])
      }
    end)
  end

  defp parse_ability_bonuses(data) do
    case Map.get(data, "ability") do
      nil -> %{}
      abilities when is_list(abilities) ->
        Enum.reduce(abilities, %{}, fn ability, acc ->
          case ability do
            [ability_name, bonus] when is_binary(ability_name) and is_integer(bonus) ->
              ability_atom = String.downcase(ability_name) |> String.to_atom()
              Map.put(acc, ability_atom, bonus)
            _ -> acc
          end
        end)
      abilities when is_map(abilities) ->
        Enum.into(abilities, %{}, fn {k, v} ->
          {String.downcase(k) |> String.to_atom(), v}
        end)
      _ -> %{}
    end
  end

  defp parse_speed(data) do
    case Map.get(data, "speed") do
      nil -> 30
      speed when is_integer(speed) -> speed
      speed when is_map(speed) -> Map.get(speed, "walk", 30)
      _ -> 30
    end
  end

  @doc """
  Parse classes.json file content.
  """
  def parse_classes(json_content) do
    case Jason.decode(json_content) do
      {:ok, %{"class" => classes}} ->
        Enum.map(classes, &parse_class/1)
      {:ok, classes} when is_list(classes) ->
        Enum.map(classes, &parse_class/1)
      error ->
        error
    end
  end

  defp parse_class(class_data) do
    %{
      name: get_string(class_data, "name"),
      source: normalize_source(get_string(class_data, "source")),
      hit_die: parse_hit_die(class_data),
      primary_ability: parse_primary_ability(class_data),
      subclasses: parse_subclasses(get_list(class_data, "subclasses", [])),
      features: parse_class_features(get_list(class_data, "classFeatures", []))
    }
  end

  defp parse_subclasses(subclasses_data) do
    Enum.map(subclasses_data, fn subclass ->
      %{
        name: get_string(subclass, "name"),
        source: normalize_source(get_string(subclass, "source")),
        short_name: get_string(subclass, "shortName")
      }
    end)
  end

  defp parse_class_features(features_data) do
    Enum.map(features_data, fn feature ->
      %{
        name: get_string(feature, "name"),
        level: get_integer(feature, "level", 1),
        entries: get_list(feature, "entries", [])
      }
    end)
  end

  defp parse_hit_die(data) do
    case Map.get(data, "hd") do
      nil -> 8
      hd when is_integer(hd) -> hd
      hd when is_map(hd) -> Map.get(hd, "number", 1) * Map.get(hd, "faces", 8)
      _ -> 8
    end
  end

  defp parse_primary_ability(data) do
    case Map.get(data, "proficiency") do
      nil -> :str
      prof when is_list(prof) ->
        case Enum.find(prof, fn p -> is_map(p) && Map.get(p, "savingThrow") end) do
          nil -> :str
          %{"savingThrow" => ability} -> String.downcase(ability) |> String.to_atom()
          _ -> :str
        end
      _ -> :str
    end
  end

  @doc """
  Parse backgrounds.json file content.
  """
  def parse_backgrounds(json_content) do
    case Jason.decode(json_content) do
      {:ok, %{"background" => backgrounds}} ->
        Enum.map(backgrounds, &parse_background/1)
      {:ok, backgrounds} when is_list(backgrounds) ->
        Enum.map(backgrounds, &parse_background/1)
      error ->
        error
    end
  end

  defp parse_background(bg_data) do
    %{
      name: get_string(bg_data, "name"),
      source: normalize_source(get_string(bg_data, "source")),
      entries: get_list(bg_data, "entries", []),
      skill_proficiencies: get_list(bg_data, "skillProficiencies", []),
      starting_equipment: get_list(bg_data, "startingEquipment", [])
    }
  end

  @doc """
  Normalize source names to standard format.
  """
  def normalize_source(source) when is_binary(source) do
    case String.upcase(source) do
      "PHB" -> "PHB"
      "XGE" -> "XGE"
      "TCE" -> "TCE"
      "SCAG" -> "SCAG"
      "VGM" -> "VGM"
      "MTF" -> "MTF"
      "EGW" -> "EGW"
      "FTD" -> "FTD"
      "SCC" -> "SCC"
      "WBW" -> "WBW"
      "SAC" -> "SAC"
      other -> other
    end
  end

  def normalize_source(_), do: "PHB"

  # Helper functions
  defp get_string(data, key, default \\ nil) do
    case Map.get(data, key) do
      nil -> default
      value when is_binary(value) -> value
      value when is_list(value) -> List.first(value) || default
      _ -> default
    end
  end

  defp get_integer(data, key, default \\ 0) do
    case Map.get(data, key) do
      nil -> default
      value when is_integer(value) -> value
      value when is_binary(value) -> String.to_integer(value)
      _ -> default
    end
  end

  defp get_list(data, key, default \\ []) do
    case Map.get(data, key) do
      nil -> default
      value when is_list(value) -> value
      _ -> default
    end
  end
end
