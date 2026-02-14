defmodule DndAppWeb.GraphQL.Resolvers.GameContent do
  alias DndApp.DB.Neo4j

  def races(_parent, args, _resolution) do
    opts = []
    opts = if Map.has_key?(args, :source), do: Keyword.put(opts, :source, args.source), else: opts
    opts = if Map.has_key?(args, :show_legacy), do: Keyword.put(opts, :show_legacy, args.show_legacy), else: opts

    case Neo4j.get_races(opts) do
      {:ok, races} -> {:ok, races}
      error -> {:error, "Failed to get races: #{inspect(error)}"}
    end
  end

  def race(_parent, %{name: name}, _resolution) do
    case Neo4j.get_races() do
      {:ok, races} ->
        race = Enum.find(races, &(&1.name == name))
        if race, do: {:ok, race}, else: {:error, "Race not found"}
      error -> {:error, "Failed to get race: #{inspect(error)}"}
    end
  end

  def classes(_parent, args, _resolution) do
    opts = []
    opts = if Map.has_key?(args, :source), do: Keyword.put(opts, :source, args.source), else: opts

    case Neo4j.get_classes(opts) do
      {:ok, classes} -> {:ok, classes}
      error -> {:error, "Failed to get classes: #{inspect(error)}"}
    end
  end

  def class(_parent, %{name: name}, _resolution) do
    case Neo4j.get_classes() do
      {:ok, classes} ->
        class = Enum.find(classes, &(&1.name == name))
        if class, do: {:ok, class}, else: {:error, "Class not found"}
      error -> {:error, "Failed to get class: #{inspect(error)}"}
    end
  end

  def backgrounds(_parent, args, _resolution) do
    opts = []
    opts = if Map.has_key?(args, :source), do: Keyword.put(opts, :source, args.source), else: opts

    case Neo4j.get_backgrounds(opts) do
      {:ok, backgrounds} -> {:ok, backgrounds}
      error -> {:error, "Failed to get backgrounds: #{inspect(error)}"}
    end
  end

  def background(_parent, %{name: name}, _resolution) do
    case Neo4j.get_backgrounds() do
      {:ok, backgrounds} ->
        background = Enum.find(backgrounds, &(&1.name == name))
        if background, do: {:ok, background}, else: {:error, "Background not found"}
      error -> {:error, "Failed to get background: #{inspect(error)}"}
    end
  end

  def class_features(parent, args, _resolution) do
    max_level = Map.get(args, :max_level)
    class_name = Map.get(parent, :name)

    if class_name do
      cypher = """
      MATCH (c:Class {name: $class_name})-[rel:GRANTS_FEATURE]->(f:Feature)
      #{if max_level, do: "WHERE rel.at_level <= $max_level", else: ""}
      RETURN f.name as name, rel.at_level as level, f.entries as entries
      ORDER BY rel.at_level
      """

      params = %{class_name: class_name}
      params = if max_level, do: Map.put(params, :max_level, max_level), else: params

      case Neo4j.query(cypher, params) do
        {:ok, records} ->
          features = Enum.map(records, fn record ->
            %{
              name: record.name,
              level: record.level,
              entries: record.entries
            }
          end)
          {:ok, features}
        error -> {:error, "Failed to get class features: #{inspect(error)}"}
      end
    else
      {:ok, []}
    end
  end
end
