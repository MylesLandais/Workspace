defmodule DndApp.TextParser do
  @moduledoc """
  Parses 5etools text format and converts tags like {@spell fireball} into
  interactive HTML elements with tooltip support.
  """

  @doc """
  Parse text containing 5etools tags and return a list of text/HTML fragments.
  Returns a list of tuples: {:text, content} or {:tag, type, name, attrs}
  """
  def parse(text) when is_binary(text) do
    Regex.split(~r/\{@(\w+)\s+([^}]+)\}/, text, include_captures: true, trim: true)
    |> Enum.reduce([], fn
      "", acc -> acc
      "{@" <> rest, acc -> acc
      tag_type, acc when tag_type in ["spell", "item", "creature", "skill", "condition"] -> acc
      tag_name, acc -> acc
      text, acc -> [{:text, text} | acc]
    end)
    |> Enum.reverse()
    |> parse_segments(text)
  end

  def parse(_), do: []

  defp parse_segments(segments, original_text) do
    Regex.scan(~r/\{@(\w+)\s+([^}]+)\}/, original_text, return: :index)
    |> Enum.reduce({[], 0}, fn [{start, length} | _] = match, {acc, last_pos} ->
      tag_text = String.slice(original_text, start, length)
      {type, name} = extract_tag_info(tag_text)

      # Add text before tag
      text_before = if start > last_pos, do: String.slice(original_text, last_pos, start - last_pos), else: ""
      new_acc = if text_before != "", do: [{:text, text_before} | acc], else: acc

      # Add tag
      new_acc = [{:tag, type, name, %{}} | new_acc]
      {new_acc, start + length}
    end)
    |> then(fn {acc, last_pos} ->
      # Add remaining text
      remaining = String.slice(original_text, last_pos, String.length(original_text))
      if remaining != "", do: [{:text, remaining} | acc], else: acc
    end)
    |> Enum.reverse()
  end

  defp extract_tag_info("{@" <> rest) do
    case Regex.run(~r/(\w+)\s+(.+)/, rest) do
      [_, type, name] -> {String.to_atom(type), String.trim(name)}
      _ -> {:unknown, rest}
    end
  end

  defp extract_tag_info(_), do: {:unknown, ""}

  @doc """
  Convert parsed segments to a list of text and tag tuples.
  Tags are returned as {:tag, type, name} for rendering in components.
  """
  def to_fragments(segments) do
    Enum.map(segments, fn
      {:text, content} -> {:text, content}
      {:tag, type, name, _attrs} -> {:tag, type, name}
    end)
  end

  @doc """
  Parse and convert text directly to fragments.
  Convenience function that combines parse/1 and to_fragments/1.
  """
  def parse_to_fragments(text) do
    text
    |> parse()
    |> to_fragments()
  end

  @doc """
  Strip all tags from text, returning plain text.
  """
  def strip_tags(text) when is_binary(text) do
    Regex.replace(~r/\{@\w+\s+[^}]+\}/, text, fn match ->
      case extract_tag_info(match) do
        {_type, name} -> name
        _ -> ""
      end
    end)
  end

  def strip_tags(_), do: ""
end
