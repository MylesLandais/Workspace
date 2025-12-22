defmodule DndApp.Dice do
  @moduledoc """
  Dice rolling engine for D&D 5e.
  Supports expressions like:
  - "4d6" - roll 4 six-sided dice
  - "1d20+5" - roll 1d20 and add 5
  - "4d6dl1" - roll 4d6 and drop lowest 1
  - "4d6dh1" - roll 4d6 and drop highest 1
  """

  @type dice_result :: %{
    expression: String.t(),
    rolls: [integer()],
    dropped: [integer()],
    modifier: integer(),
    total: integer()
  }

  @doc """
  Roll dice based on an expression string.

  Examples:
  - "4d6" -> rolls 4 six-sided dice
  - "1d20+5" -> rolls 1d20 and adds 5
  - "4d6dl1" -> rolls 4d6 and drops the lowest 1
  - "2d20dh1" -> rolls 2d20 and drops the highest 1
  - "1d8+2" -> rolls 1d8 and adds 2
  """
  @spec roll(String.t()) :: {:ok, dice_result()} | {:error, String.t()}
  def roll(expression) when is_binary(expression) do
    case parse_expression(expression) do
      {:ok, parsed} ->
        result = execute_roll(parsed)
        {:ok, result}
      error -> error
    end
  end

  @doc """
  Roll ability scores using the standard 4d6 drop lowest method.
  Returns 6 ability score values.
  """
  @spec roll_ability_scores() :: [integer()]
  def roll_ability_scores do
    for _ <- 1..6 do
      case roll("4d6dl1") do
        {:ok, result} -> result.total
        _ -> 10  # fallback
      end
    end
  end

  @doc """
  Roll a single ability score using 4d6 drop lowest.
  """
  @spec roll_ability_score() :: integer()
  def roll_ability_score do
    case roll("4d6dl1") do
      {:ok, result} -> result.total
      _ -> 10  # fallback
    end
  end

  defp parse_expression(expr) do
    # Remove whitespace
    expr = String.trim(expr)

    # Parse drop lowest/highest
    {expr, drop_lowest, drop_highest} = parse_drop(expr)

    # Parse modifier
    {expr, modifier} = parse_modifier(expr)

    # Parse dice expression (XdY)
    case Regex.run(~r/^(\d+)d(\d+)$/i, expr) do
      [_, count_str, sides_str] ->
        count = String.to_integer(count_str)
        sides = String.to_integer(sides_str)

        if count > 0 and count <= 100 and sides > 0 and sides <= 1000 do
          {:ok, %{
            count: count,
            sides: sides,
            drop_lowest: drop_lowest,
            drop_highest: drop_highest,
            modifier: modifier,
            original: expr
          }}
        else
          {:error, "Invalid dice count or sides (max 100 dice, 1000 sides)"}
        end
      _ ->
        {:error, "Invalid dice expression. Use format like '4d6', '1d20+5', or '4d6dl1'"}
    end
  end

  defp parse_drop(expr) do
    cond do
      String.contains?(expr, "dl") ->
        case Regex.run(~r/dl(\d+)$/i, expr) do
          [_, n_str] ->
            n = String.to_integer(n_str)
            expr = String.replace(expr, ~r/dl\d+$/i, "")
            {expr, n, 0}
          _ -> {expr, 0, 0}
        end
      String.contains?(expr, "dh") ->
        case Regex.run(~r/dh(\d+)$/i, expr) do
          [_, n_str] ->
            n = String.to_integer(n_str)
            expr = String.replace(expr, ~r/dh\d+$/i, "")
            {expr, 0, n}
          _ -> {expr, 0, 0}
        end
      true ->
        {expr, 0, 0}
    end
  end

  defp parse_modifier(expr) do
    cond do
      String.contains?(expr, "+") ->
        case Regex.run(~r/\+(\d+)$/, expr) do
          [_, mod_str] ->
            mod = String.to_integer(mod_str)
            expr = String.replace(expr, ~r/\+\d+$/, "")
            {expr, mod}
          _ -> {expr, 0}
        end
      String.contains?(expr, "-") ->
        case Regex.run(~r/-(\d+)$/, expr) do
          [_, mod_str] ->
            mod = -String.to_integer(mod_str)
            expr = String.replace(expr, ~r/-\d+$/, "")
            {expr, mod}
          _ -> {expr, 0}
        end
      true ->
        {expr, 0}
    end
  end

  defp execute_roll(parsed) do
    # Roll all dice
    rolls = for _ <- 1..parsed.count do
      :rand.uniform(parsed.sides)
    end

    # Sort for dropping
    sorted_rolls = Enum.sort(rolls)

    # Drop lowest
    {remaining_rolls, dropped_lowest} =
      if parsed.drop_lowest > 0 do
        {dropped, kept} = Enum.split(sorted_rolls, parsed.drop_lowest)
        {kept, dropped}
      else
        {sorted_rolls, []}
      end

    # Drop highest
    {final_rolls, dropped_highest} =
      if parsed.drop_highest > 0 do
        reversed = Enum.reverse(remaining_rolls)
        {dropped, kept} = Enum.split(reversed, parsed.drop_highest)
        {Enum.reverse(kept), Enum.reverse(dropped)}
      else
        {remaining_rolls, []}
      end

    total = Enum.sum(final_rolls) + parsed.modifier

    %{
      expression: build_expression_string(parsed),
      rolls: rolls,
      dropped: dropped_lowest ++ dropped_highest,
      modifier: parsed.modifier,
      total: total
    }
  end

  defp build_expression_string(parsed) do
    base = "#{parsed.count}d#{parsed.sides}"
    drop_part = cond do
      parsed.drop_lowest > 0 -> "dl#{parsed.drop_lowest}"
      parsed.drop_highest > 0 -> "dh#{parsed.drop_highest}"
      true -> ""
    end
    mod_part = cond do
      parsed.modifier > 0 -> "+#{parsed.modifier}"
      parsed.modifier < 0 -> "#{parsed.modifier}"
      true -> ""
    end
    base <> drop_part <> mod_part
  end
end
