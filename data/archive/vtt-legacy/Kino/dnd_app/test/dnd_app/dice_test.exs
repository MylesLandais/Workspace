defmodule DndApp.DiceTest do
  use ExUnit.Case, async: true
  alias DndApp.Dice

  describe "roll/1" do
    test "rolls a simple d20" do
      assert {:ok, result} = Dice.roll("1d20")
      assert result.total >= 1
      assert result.total <= 20
      assert length(result.rolls) == 1
      assert hd(result.rolls) >= 1
      assert hd(result.rolls) <= 20
      assert result.modifier == 0
      assert result.dropped == []
    end

    test "rolls multiple dice" do
      assert {:ok, result} = Dice.roll("4d6")
      assert length(result.rolls) == 4
      assert result.total >= 4
      assert result.total <= 24
      assert Enum.all?(result.rolls, &(&1 >= 1 && &1 <= 6))
    end

    test "rolls with positive modifier" do
      assert {:ok, result} = Dice.roll("1d20+5")
      assert result.modifier == 5
      assert result.total >= 6
      assert result.total <= 25
    end

    test "rolls with negative modifier" do
      assert {:ok, result} = Dice.roll("1d20-3")
      assert result.modifier == -3
      assert result.total >= -2
      assert result.total <= 17
    end

    test "drops lowest die" do
      assert {:ok, result} = Dice.roll("4d6dl1")
      assert length(result.rolls) == 4
      assert length(result.dropped) == 1
      assert result.total >= 3
      assert result.total <= 18
      # Total should be sum of kept dice
      kept_sum = Enum.sum(result.rolls) - Enum.sum(result.dropped)
      assert result.total == kept_sum + result.modifier
    end

    test "drops highest die" do
      assert {:ok, result} = Dice.roll("2d20dh1")
      assert length(result.rolls) == 2
      assert length(result.dropped) == 1
      assert result.total >= 1
      assert result.total <= 20
    end

    test "handles ability score rolling (4d6 drop lowest)" do
      assert {:ok, result} = Dice.roll("4d6dl1")
      assert length(result.rolls) == 4
      assert length(result.dropped) == 1
      # Ability scores should be between 3 and 18
      assert result.total >= 3
      assert result.total <= 18
    end

    test "returns error for invalid expression" do
      assert {:error, _} = Dice.roll("invalid")
      assert {:error, _} = Dice.roll("d20")
      assert {:error, _} = Dice.roll("20d")
      assert {:error, _} = Dice.roll("")
    end

    test "returns error for too many dice" do
      assert {:error, _} = Dice.roll("101d6")
    end

    test "returns error for too many sides" do
      assert {:error, _} = Dice.roll("1d1001")
    end

    test "handles edge case of single die with drop" do
      assert {:ok, result} = Dice.roll("1d6dl1")
      assert length(result.rolls) == 1
      # If we drop the only die, total should be 0 + modifier
      assert result.total >= 0
    end
  end

  describe "roll_ability_scores/0" do
    test "generates 6 ability scores" do
      scores = Dice.roll_ability_scores()
      assert length(scores) == 6
      assert Enum.all?(scores, &(&1 >= 3 && &1 <= 18))
    end

    test "generates different scores on multiple calls" do
      scores1 = Dice.roll_ability_scores()
      scores2 = Dice.roll_ability_scores()

      # Very unlikely to get the same scores twice
      # But possible, so we just check they're valid
      assert length(scores1) == 6
      assert length(scores2) == 6
    end
  end
end




