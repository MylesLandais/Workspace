defmodule DndApp.RandomGenerator do
  @moduledoc """
  Procedural character generator for random character creation.
  """
  alias DndApp.Characters
  alias DndApp.Dice
  alias DndApp.NameGenerator

  @doc """
  Generate a random character with optional constraints.
  """
  def generate(opts \\ []) do
    level = Keyword.get(opts, :level, 1)
    class_constraint = Keyword.get(opts, :class, nil)

    race = random_race()
    class = if class_constraint, do: class_constraint, else: random_class()
    background = random_background()
    name = NameGenerator.random_name(race.name)

    ability_scores = generate_ability_scores()

    %{
      name: name,
      race: race.name,
      class: class.name,
      background: background,
      level: level,
      base_scores: ability_scores,
      ability_method: :manual
    }
  end

  defp random_race do
    races = Characters.races()
    Enum.random(races)
  end

  defp random_class do
    classes = Characters.classes()
    Enum.random(classes)
  end

  defp random_background do
    backgrounds = Characters.backgrounds()
    Enum.random(backgrounds)
  end

  defp generate_ability_scores do
    # Use 4d6 drop lowest for each ability
    %{
      str: Dice.roll_ability_score(),
      dex: Dice.roll_ability_score(),
      con: Dice.roll_ability_score(),
      int: Dice.roll_ability_score(),
      wis: Dice.roll_ability_score(),
      cha: Dice.roll_ability_score()
    }
  end
end
