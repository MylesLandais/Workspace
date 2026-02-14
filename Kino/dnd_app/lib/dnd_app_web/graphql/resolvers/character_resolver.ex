defmodule DndAppWeb.GraphQL.Resolvers.Character do
  alias DndApp.Characters
  alias DndApp.DB.Neo4j

  def list(_parent, _args, _resolution) do
    case Neo4j.list_characters() do
      {:ok, characters} -> {:ok, characters}
      error -> {:error, "Failed to list characters: #{inspect(error)}"}
    end
  end

  def get(_parent, %{id: id}, _resolution) do
    case Neo4j.get_character(id) do
      {:ok, character} -> {:ok, character}
      {:error, :not_found} -> {:error, "Character not found"}
      error -> {:error, "Failed to get character: #{inspect(error)}"}
    end
  end
end
