defmodule DndApp.CharactersTest do
  use ExUnit.Case, async: true
  alias DndApp.Characters

  describe "ability_modifier/1" do
    test "calculates modifier for score 10" do
      assert Characters.ability_modifier(10) == 0
    end

    test "calculates modifier for score 12" do
      assert Characters.ability_modifier(12) == 1
    end

    test "calculates modifier for score 8" do
      assert Characters.ability_modifier(8) == -1
    end

    test "calculates modifier for score 20" do
      assert Characters.ability_modifier(20) == 5
    end

    test "calculates modifier for score 1" do
      assert Characters.ability_modifier(1) == -5
    end

    test "calculates modifier for odd scores" do
      assert Characters.ability_modifier(13) == 1
      assert Characters.ability_modifier(15) == 2
      assert Characters.ability_modifier(17) == 3
    end
  end

  describe "proficiency_bonus/1" do
    test "calculates proficiency bonus for level 1" do
      assert Characters.proficiency_bonus(1) == 2
    end

    test "calculates proficiency bonus for level 5" do
      assert Characters.proficiency_bonus(5) == 3
    end

    test "calculates proficiency bonus for level 9" do
      assert Characters.proficiency_bonus(9) == 4
    end

    test "calculates proficiency bonus for level 13" do
      assert Characters.proficiency_bonus(13) == 5
    end

    test "calculates proficiency bonus for level 17" do
      assert Characters.proficiency_bonus(17) == 6
    end

    test "calculates proficiency bonus for level 20" do
      assert Characters.proficiency_bonus(20) == 6
    end
  end

  describe "apply_race_bonuses/2" do
    test "applies Human bonuses (+1 to all)" do
      base = %{str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10}
      result = Characters.apply_race_bonuses(base, "Human")

      assert result.str == 11
      assert result.dex == 11
      assert result.con == 11
      assert result.int == 11
      assert result.wis == 11
      assert result.cha == 11
    end

    test "applies Elf bonuses (+2 DEX, +1 WIS)" do
      base = %{str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10}
      result = Characters.apply_race_bonuses(base, "Elf")

      assert result.str == 10
      assert result.dex == 12
      assert result.con == 10
      assert result.int == 10
      assert result.wis == 11
      assert result.cha == 10
    end

    test "applies Dwarf bonuses (+2 CON, +1 STR)" do
      base = %{str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10}
      result = Characters.apply_race_bonuses(base, "Dwarf")

      assert result.str == 11
      assert result.dex == 10
      assert result.con == 12
      assert result.int == 10
      assert result.wis == 10
      assert result.cha == 10
    end

    test "returns unchanged scores for unknown race" do
      base = %{str: 15, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      result = Characters.apply_race_bonuses(base, "Unknown Race")

      assert result == base
    end
  end

  describe "calculate_starting_hp/3" do
    test "calculates HP for level 1 Barbarian with +2 CON" do
      hp = Characters.calculate_starting_hp("Barbarian", 2, 1)
      # Barbarian has d12 hit die, so 12 + 2 = 14
      assert hp == 14
    end

    test "calculates HP for level 1 Wizard with -1 CON" do
      hp = Characters.calculate_starting_hp("Wizard", -1, 1)
      # Wizard has d6 hit die, so 6 - 1 = 5 (minimum 1)
      assert hp == 5
    end

    test "calculates HP for level 1 Fighter with +0 CON" do
      hp = Characters.calculate_starting_hp("Fighter", 0, 1)
      # Fighter has d10 hit die, so 10 + 0 = 10
      assert hp == 10
    end

    test "calculates HP for level 5 character" do
      hp = Characters.calculate_starting_hp("Fighter", 2, 5)
      # Level 1: 10 + 2 = 12
      # Levels 2-5: 4 * (6 + 2) = 32 (average of d10 is 6)
      # Total: 12 + 32 = 44
      assert hp == 44
    end

    test "handles unknown class with default hit die" do
      hp = Characters.calculate_starting_hp("Unknown", 0, 1)
      # Default hit die is 8
      assert hp == 8
    end
  end

  describe "calculate_ac/2" do
    test "calculates base AC with DEX modifier" do
      assert Characters.calculate_ac(3) == 13  # 10 + 3
      assert Characters.calculate_ac(0) == 10    # 10 + 0
      assert Characters.calculate_ac(-1) == 9   # 10 - 1
    end

    test "handles armor parameter (simplified for MVP)" do
      # For MVP, armor doesn't affect AC calculation
      assert Characters.calculate_ac(2, :leather) == 12
    end
  end

  describe "get_race/1" do
    test "returns race data for valid race" do
      race = Characters.get_race("Human")
      assert race.name == "Human"
      assert race.ability_bonuses.str == 1
    end

    test "returns nil for invalid race" do
      assert Characters.get_race("Invalid Race") == nil
    end
  end

  describe "get_class/1" do
    test "returns class data for valid class" do
      class = Characters.get_class("Fighter")
      assert class.name == "Fighter"
      assert class.hit_die == 10
      assert class.primary_ability == :str
    end

    test "returns nil for invalid class" do
      assert Characters.get_class("Invalid Class") == nil
    end
  end

  describe "generate_ability_scores/0" do
    test "generates 6 ability scores" do
      scores = Characters.generate_ability_scores()
      assert length(scores) == 6
      assert Enum.all?(scores, &(&1 >= 3 && &1 <= 18))
    end
  end
end




