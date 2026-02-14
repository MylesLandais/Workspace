defmodule DndAppWeb.GraphQL.Schema do
  use Absinthe.Schema

  import_types DndAppWeb.GraphQL.Types

  query do
    field :characters, list_of(:character) do
      resolve &DndAppWeb.GraphQL.Resolvers.Character.list/2
    end

    field :character, :character do
      arg :id, non_null(:id)
      resolve &DndAppWeb.GraphQL.Resolvers.Character.get/2
    end

    field :races, list_of(:race) do
      arg :source, :string
      arg :show_legacy, :boolean, default_value: false
      resolve &DndAppWeb.GraphQL.Resolvers.GameContent.races/2
    end

    field :race, :race do
      arg :name, non_null(:string)
      resolve &DndAppWeb.GraphQL.Resolvers.GameContent.race/2
    end

    field :classes, list_of(:class) do
      arg :source, :string
      resolve &DndAppWeb.GraphQL.Resolvers.GameContent.classes/2
    end

    field :class, :class do
      arg :name, non_null(:string)
      resolve &DndAppWeb.GraphQL.Resolvers.GameContent.class/2
    end

    field :backgrounds, list_of(:background) do
      arg :source, :string
      resolve &DndAppWeb.GraphQL.Resolvers.GameContent.backgrounds/2
    end

    field :background, :background do
      arg :name, non_null(:string)
      resolve &DndAppWeb.GraphQL.Resolvers.GameContent.background/2
    end
  end
end
