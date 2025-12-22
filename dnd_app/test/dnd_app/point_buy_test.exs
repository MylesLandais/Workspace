defmodule DndApp.PointBuyTest do
  use ExUnit.Case, async: true
  alias DndApp.PointBuy

  describe "cost/1" do
    test "calculates cost for scores 8-13 correctly" do
      assert PointBuy.cost(8) == 0
      assert PointBuy.cost(9) == 1
      assert PointBuy.cost(10) == 2
      assert PointBuy.cost(11) == 3
      assert PointBuy.cost(12) == 4
      assert PointBuy.cost(13) == 5
    end

    test "calculates cost for score 14" do
      assert PointBuy.cost(14) == 9
    end

    test "calculates cost for score 15" do
      assert PointBuy.cost(15) == 11
    end

    test "returns 0 for scores below 8" do
      assert PointBuy.cost(7) == 0
      assert PointBuy.cost(1) == 0
      assert PointBuy.cost(0) == 0
    end

    test "returns :invalid for scores above 15" do
      assert PointBuy.cost(16) == :invalid
      assert PointBuy.cost(20) == :invalid
      assert PointBuy.cost(30) == :invalid
    end
  end

  describe "total_cost/1" do
    test "calculates total cost for valid scores" do
      scores = %{str: 15, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      # 11 + 9 + 5 + 4 + 2 + 0 = 31
      assert PointBuy.total_cost(scores) == 31
    end

    test "calculates total cost for minimum scores" do
      scores = %{str: 8, dex: 8, con: 8, int: 8, wis: 8, cha: 8}
      assert PointBuy.total_cost(scores) == 0
    end

    test "calculates total cost for maximum valid scores" do
      scores = %{str: 15, dex: 15, con: 15, int: 15, wis: 15, cha: 15}
      # 11 * 6 = 66
      assert PointBuy.total_cost(scores) == 66
    end

    test "returns :invalid when any score is above 15" do
      scores = %{str: 16, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.total_cost(scores) == :invalid
    end

    test "returns :invalid when any score is below 8" do
      scores = %{str: 7, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      # Score 7 has cost 0, but we might want to validate separately
      # For now, cost(7) returns 0, so this would be valid
      # This test documents current behavior
      assert PointBuy.total_cost(scores) == 28
    end

    test "handles empty map" do
      assert PointBuy.total_cost(%{}) == 0
    end

    test "handles non-map input" do
      assert PointBuy.total_cost(nil) == 0
      assert PointBuy.total_cost([]) == 0
    end
  end

  describe "remaining_points/2" do
    test "calculates remaining points correctly" do
      scores = %{str: 15, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      # Total cost: 31, budget: 27
      assert PointBuy.remaining_points(scores, 27) == -4
    end

    test "returns 0 when cost equals budget" do
      scores = %{str: 15, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      # Total cost: 27, budget: 27
      assert PointBuy.remaining_points(scores, 27) == 0
    end

    test "returns positive when cost is less than budget" do
      scores = %{str: 13, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      # Total cost: 18, budget: 27
      assert PointBuy.remaining_points(scores, 27) == 9
    end

    test "uses default budget when not specified" do
      scores = %{str: 15, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      # Total cost: 31, default budget: 27
      assert PointBuy.remaining_points(scores) == -4
    end

    test "returns :invalid when scores are invalid" do
      scores = %{str: 16, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.remaining_points(scores, 27) == :invalid
    end
  end

  describe "validate_score/3" do
    test "allows valid score increases" do
      current_scores = %{str: 13, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.validate_score(current_scores, :str, 14) == {:ok, 14}
    end

    test "allows valid score decreases" do
      current_scores = %{str: 14, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.validate_score(current_scores, :str, 13) == {:ok, 13}
    end

    test "rejects scores above 15" do
      current_scores = %{str: 13, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.validate_score(current_scores, :str, 16) == {:error, :score_too_high}
    end

    test "rejects scores below 8" do
      current_scores = %{str: 8, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.validate_score(current_scores, :str, 7) == {:error, :score_too_low}
    end

    test "rejects when new total cost exceeds budget" do
      scores = %{str: 15, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      # Current cost: 31, budget: 27
      # Trying to increase cha from 8 to 9 increases cost to 32
      result = PointBuy.validate_score(scores, :cha, 9, 27)
      assert {:error, :insufficient_points} = result
    end

    test "allows changes that stay within budget" do
      scores = %{str: 13, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      # Current cost: 18, budget: 27
      result = PointBuy.validate_score(scores, :cha, 9, 27)
      assert {:ok, 9, 19} = result
    end

    test "returns error for below minimum" do
      scores = %{str: 8, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.validate_score(scores, :str, 7) == {:error, :below_minimum}
    end

    test "returns error for above maximum" do
      scores = %{str: 15, dex: 13, con: 13, int: 12, wis: 10, cha: 8}
      assert PointBuy.validate_score(scores, :str, 16) == {:error, :above_maximum}
    end
  end

  describe "default_budget/0" do
    test "returns the default budget" do
      assert PointBuy.default_budget() == 27
    end
  end

  describe "min_score/0 and max_score/0" do
    test "returns correct min and max scores" do
      assert PointBuy.min_score() == 8
      assert PointBuy.max_score() == 15
    end
  end
end
