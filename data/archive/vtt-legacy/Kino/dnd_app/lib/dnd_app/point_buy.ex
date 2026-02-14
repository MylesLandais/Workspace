defmodule DndApp.PointBuy do
  @moduledoc """
  Point buy system for ability score generation.
  Implements D&D 5e point buy rules.
  """

  @default_budget 27
  @min_score 8
  @max_score 15

  @doc """
  Calculate the point cost for a single ability score.
  Rules:
  - Scores 8-13: cost = score - 8 (1 point per increase)
  - Score 14: cost = 7 + 2 = 9 points
  - Score 15: cost = 9 + 2 = 11 points
  """
  def cost(score) when score >= 8 and score <= 13 do
    score - 8
  end

  def cost(14), do: 9
  def cost(15), do: 11
  def cost(score) when score < 8, do: 0
  def cost(score) when score > 15, do: :invalid

  @doc """
  Calculate total cost for all ability scores.
  """
  def total_cost(scores) when is_map(scores) do
    scores
    |> Map.values()
    |> Enum.map(&cost/1)
    |> Enum.reduce(0, fn
      :invalid, _acc -> :invalid
      cost, acc -> acc + cost
    end)
  end

  def total_cost(_), do: 0

  @doc """
  Calculate remaining points from budget.
  """
  def remaining_points(scores, budget \\ @default_budget) do
    case total_cost(scores) do
      :invalid -> :invalid
      cost -> budget - cost
    end
  end

  @doc """
  Validate if a score increase is allowed.
  Returns {:ok, new_score, new_cost} or {:error, reason}
  """
  def validate_score(current_scores, ability, new_score, budget \\ @default_budget) do
    cond do
      new_score < @min_score ->
        {:error, :below_minimum}

      new_score > @max_score ->
        {:error, :above_maximum}

      true ->
        current_cost = total_cost(current_scores)
        new_scores = Map.put(current_scores, ability, new_score)
        new_cost = total_cost(new_scores)

        case new_cost do
          :invalid ->
            {:error, :invalid_score}

          cost when cost > budget ->
            {:error, :insufficient_points}

          cost ->
            {:ok, new_score, cost}
        end
    end
  end

  @doc """
  Get the default budget.
  """
  def default_budget, do: @default_budget

  @doc """
  Get min and max scores.
  """
  def min_score, do: @min_score
  def max_score, do: @max_score
end
