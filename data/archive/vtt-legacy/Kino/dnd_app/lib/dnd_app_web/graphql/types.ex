defmodule DndAppWeb.GraphQL.Types do
  use Absinthe.Schema.Notation

  object :character do
    field :id, non_null(:id)
    field :name, non_null(:string)
    field :level, non_null(:integer)
    field :race, :string
    field :class, :string
    field :background, :string
    field :str, non_null(:integer)
    field :dex, non_null(:integer)
    field :con, non_null(:integer)
    field :int, non_null(:integer)
    field :wis, non_null(:integer)
    field :cha, non_null(:integer)
    field :str_mod, non_null(:integer)
    field :dex_mod, non_null(:integer)
    field :con_mod, non_null(:integer)
    field :int_mod, non_null(:integer)
    field :wis_mod, non_null(:integer)
    field :cha_mod, non_null(:integer)
    field :proficiency_bonus, non_null(:integer)
    field :ac, non_null(:integer)
    field :max_hp, non_null(:integer)
    field :current_hp, non_null(:integer)
    field :skills, list_of(:string)
    field :race_node, :race, resolve: fn parent, _, _ -> {:ok, Map.get(parent, :race_node)} end
    field :class_node, :class, resolve: fn parent, _, _ -> {:ok, Map.get(parent, :class_node)} end
    field :background_node, :background, resolve: fn parent, _, _ -> {:ok, Map.get(parent, :background_node)} end
  end

  object :race do
    field :name, non_null(:string)
    field :source, :string
    field :size, :string
    field :speed, :integer
    field :ability_bonuses, :json
    field :subraces, list_of(:subrace), resolve: fn parent, _, _ -> {:ok, Map.get(parent, :subraces, [])} end
  end

  object :subrace do
    field :name, non_null(:string)
    field :source, :string
    field :ability_bonuses, :json
  end

  object :class do
    field :name, non_null(:string)
    field :source, :string
    field :hit_die, :integer
    field :primary_ability, :string
    field :subclasses, list_of(:subclass), resolve: fn parent, _, _ -> {:ok, Map.get(parent, :subclasses, [])} end
    field :features, list_of(:feature) do
      arg :max_level, :integer
      resolve &DndAppWeb.GraphQL.Resolvers.GameContent.class_features/2
    end
  end

  object :subclass do
    field :name, non_null(:string)
    field :source, :string
    field :short_name, :string
  end

  object :background do
    field :name, non_null(:string)
    field :source, :string
    field :description, :string
    field :skill_proficiencies, list_of(:string)
    field :starting_equipment, list_of(:string)
  end

  object :feature do
    field :name, non_null(:string)
    field :level, :integer
    field :entries, :json
  end

  scalar :json do
    parse fn
      %Absinthe.Blueprint.Input.String{value: value} ->
        case Jason.decode(value) do
          {:ok, result} -> {:ok, result}
          error -> error
        end
      %Absinthe.Blueprint.Input.Null{} -> {:ok, nil}
      _ -> {:error, "Invalid JSON"}
    end
    serialize &Jason.encode!/1
  end
end
