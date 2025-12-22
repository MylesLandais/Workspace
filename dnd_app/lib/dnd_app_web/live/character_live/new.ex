defmodule DndAppWeb.CharacterLive.New do
  use DndAppWeb, :live_view
  alias DndApp.Characters
  alias DndApp.PointBuy
  alias DndApp.NameGenerator
  alias DndApp.RulesEngine
  alias DndApp.RandomGenerator
  alias DndAppWeb.NordicComponents

  @steps [:origin, :path, :constitution, :inventory]

  @impl true
  def mount(params, _session, socket) do
    mode = parse_mode(params)
    beginner = Map.get(params, "beginner") == "true"
    template_id = Map.get(params, "template")

    character = initialize_character(mode, template_id)

    initial_step = case mode do
      :quick -> :origin
      :random -> :inventory  # Random mode generates everything, go to inventory
      _ -> :origin
    end

    {:ok,
     socket
     |> assign(:mode, mode)
     |> assign(:beginner_mode, beginner)
     |> assign(:step, initial_step)
     |> assign(:character, character)
     |> assign(:races, [])
     |> assign(:classes, [])
     |> assign(:backgrounds, [])
     |> assign(:name_suggestions, [])
     |> assign(:source_filter, nil)
     |> assign(:show_legacy, false)
     |> assign(:point_buy_budget, PointBuy.default_budget())
     |> assign(:saving, false)
     |> assign(:expanded_race, nil)
     |> assign(:show_class_details, false)
     |> assign(:selected_class, nil)
     |> assign(:tooltip, nil)
     |> assign(:expanded_packs, MapSet.new())
     |> load_game_data()}
  end

  defp initialize_character(:random, _template_id) do
    RandomGenerator.generate()
  end

  defp initialize_character(:quick, _template_id) do
    # Quick mode: minimal defaults
    %{
      name: "",
      class: nil,
      background: "Folk Hero",
      race: nil,
      subrace: nil,
      ability_method: :standard_array,
      base_scores: %{str: 15, dex: 14, con: 13, int: 12, wis: 10, cha: 8},
      overrides: %{},
      equipment: []
    }
  end

  defp initialize_character(_mode, template_id) when is_binary(template_id) do
    # Load from template (future implementation)
    %{
      name: "",
      class: nil,
      background: nil,
      race: nil,
      subrace: nil,
      ability_method: :point_buy,
      base_scores: %{str: 8, dex: 8, con: 8, int: 8, wis: 8, cha: 8},
      overrides: %{},
      equipment: []
    }
  end

  defp initialize_character(_mode, _template_id) do
    %{
      name: "",
      class: nil,
      background: nil,
      race: nil,
      subrace: nil,
      ability_method: :point_buy,
      base_scores: %{str: 8, dex: 8, con: 8, int: 8, wis: 8, cha: 8},
      overrides: %{},
      equipment: []
    }
  end

  defp parse_mode(params) do
    case Map.get(params, "mode") do
      "quick" -> :quick
      "random" -> :random
      "premade" -> :premade
      _ -> :standard
    end
  end

  defp load_game_data(socket) do
    races = Characters.races(show_legacy: socket.assigns.show_legacy, source: socket.assigns.source_filter)
    classes = Characters.classes(source: socket.assigns.source_filter)
    backgrounds = Characters.backgrounds(source: socket.assigns.source_filter)

    socket
    |> assign(:races, races)
    |> assign(:classes, classes)
    |> assign(:backgrounds, backgrounds)
  end

  @impl true
  def handle_event("goto_step", %{"step" => step_str}, socket) do
    step = String.to_atom(step_str)
    if step in @steps do
      {:noreply, assign(socket, :step, step)}
    else
      {:noreply, socket}
    end
  end

  @impl true
  def handle_event("prev_step", _params, socket) do
    current_index = Enum.find_index(@steps, &(&1 == socket.assigns.step))
    if current_index > 0 do
      prev_step = Enum.at(@steps, current_index - 1)
      {:noreply, assign(socket, :step, prev_step)}
    else
      {:noreply, socket}
    end
  end

  @impl true
  def handle_event("next_step", _params, socket) do
    if can_proceed?(socket) do
      current_index = Enum.find_index(@steps, &(&1 == socket.assigns.step))
      if current_index < length(@steps) - 1 do
        next_step = Enum.at(@steps, current_index + 1)
        {:noreply, assign(socket, :step, next_step)}
      else
        # Last step - create character
        handle_event("create_character", %{}, socket)
      end
    else
      {:noreply, put_flash(socket, :error, "Please complete required fields")}
    end
  end

  @impl true
  def handle_event("toggle_race_expansion", %{"race_name" => race_name}, socket) do
    expanded = if socket.assigns.expanded_race == race_name, do: nil, else: race_name
    {:noreply, assign(socket, :expanded_race, expanded)}
  end

  @impl true
  def handle_event("show_class_details", %{"class_name" => class_name}, socket) do
    {:noreply,
     socket
     |> assign(:show_class_details, true)
     |> assign(:selected_class, class_name)}
  end

  @impl true
  def handle_event("hide_class_details", _params, socket) do
    {:noreply,
     socket
     |> assign(:show_class_details, false)
     |> assign(:selected_class, nil)}
  end

  @impl true
  def handle_event("show_tooltip", %{"type" => type, "name" => name}, socket) do
    {:noreply, assign(socket, :tooltip, %{type: type, name: name})}
  end

  @impl true
  def handle_event("hide_tooltip", _params, socket) do
    {:noreply, assign(socket, :tooltip, nil)}
  end

  @impl true
  def handle_event("toggle_pack", %{"pack_name" => pack_name}, socket) do
    expanded = socket.assigns.expanded_packs
    new_expanded = if MapSet.member?(expanded, pack_name) do
      MapSet.delete(expanded, pack_name)
    else
      MapSet.put(expanded, pack_name)
    end
    {:noreply, assign(socket, :expanded_packs, new_expanded)}
  end

  @impl true
  def handle_event("toggle_equipment", %{"item_name" => item_name}, socket) do
    equipment = socket.assigns.character.equipment || []
    new_equipment = if item_name in equipment do
      List.delete(equipment, item_name)
    else
      [item_name | equipment]
    end
    character = update_in(socket.assigns.character.equipment, fn _ -> new_equipment end)
    {:noreply, assign(socket, :character, character)}
  end

  defp can_proceed?(socket) do
    case socket.assigns.step do
      :origin -> socket.assigns.character.name != "" && socket.assigns.character.name != nil && socket.assigns.character.race != nil
      :path -> socket.assigns.character.class != nil && socket.assigns.character.background != nil
      :constitution -> valid_ability_scores?(socket.assigns.character)
      :inventory -> true
      _ -> false
    end
  end

  defp valid_ability_scores?(character) do
    scores = character.base_scores
    map_size(scores) == 6 &&
      Enum.all?(scores, fn {_k, v} -> v >= 8 && v <= 15 end) &&
      PointBuy.total_cost(scores) <= PointBuy.default_budget()
  end

  @impl true
  def handle_event("select_class", %{"class_name" => class_name}, socket) do
    character = update_in(socket.assigns.character.class, fn _ -> class_name end)
    {:noreply, assign(socket, :character, character)}
  end

  @impl true
  def handle_event("select_background", %{"background" => background}, socket) do
    character = update_in(socket.assigns.character.background, fn _ -> background end)
    {:noreply, assign(socket, :character, character)}
  end

  @impl true
  def handle_event("select_race", %{"race_name" => race_name}, socket) do
    character = update_in(socket.assigns.character.race, fn _ -> race_name end)
    {:noreply, assign(socket, :character, character)}
  end

  @impl true
  def handle_event("select_subrace", %{"subrace_name" => subrace_name}, socket) do
    character = update_in(socket.assigns.character.subrace, fn _ -> subrace_name end)
    {:noreply, assign(socket, :character, character)}
  end

  @impl true
  def handle_event("update_name", params, socket) do
    name = Map.get(params, "value") || Map.get(params, "name") || ""
    character = update_in(socket.assigns.character.name, fn _ -> name end)
    {:noreply, assign(socket, :character, character)}
  end

  @impl true
  def handle_event("select_name", %{"name" => name}, socket) do
    character = update_in(socket.assigns.character.name, fn _ -> name end)
    {:noreply, assign(socket, :character, character)}
  end

  @impl true
  def handle_event("suggest_names", %{"race" => race}, socket) do
    suggestions = NameGenerator.suggest_names(race, count: 5)
    {:noreply, assign(socket, :name_suggestions, suggestions)}
  end

  @impl true
  def handle_event("set_ability_method", %{"method" => method_str}, socket) do
    method = String.to_atom(method_str)
    character = update_in(socket.assigns.character.ability_method, fn _ -> method end)

    # Initialize scores based on method
    base_scores = case method do
      :standard_array -> %{str: 15, dex: 14, con: 13, int: 12, wis: 10, cha: 8}
      :point_buy -> %{str: 8, dex: 8, con: 8, int: 8, wis: 8, cha: 8}
      :manual -> %{str: 8, dex: 8, con: 8, int: 8, wis: 8, cha: 8}
    end

    character = update_in(character.base_scores, fn _ -> base_scores end)
    {:noreply, assign(socket, :character, character)}
  end

  @impl true
  def handle_event("update_ability_score", %{"ability" => ability_str} = params, socket) do
    ability = String.to_atom(ability_str)
    value = case Map.get(params, "value") do
      val when is_binary(val) -> String.to_integer(val)
      val when is_integer(val) -> val
      _ -> Map.get(socket.assigns.character.base_scores, ability, 8)
    end

    case socket.assigns.character.ability_method do
      :point_buy ->
        current_scores = socket.assigns.character.base_scores
        case PointBuy.validate_score(current_scores, ability, value, PointBuy.default_budget()) do
          {:ok, new_score, _cost} ->
            character = update_in(socket.assigns.character.base_scores[ability], fn _ -> new_score end)
            {:noreply, assign(socket, :character, character)}
          {:error, reason} ->
            message = case reason do
              :below_minimum -> "Score cannot be below 8"
              :above_maximum -> "Score cannot be above 15"
              :insufficient_points -> "Not enough points remaining"
              _ -> "Invalid score"
            end
            {:noreply, put_flash(socket, :error, message)}
        end
      _ ->
        character = update_in(socket.assigns.character.base_scores[ability], fn _ -> value end)
        {:noreply, assign(socket, :character, character)}
    end
  end

  @impl true
  def handle_event("filter_source", %{"source" => source}, socket) do
    source_filter = if source == "", do: nil, else: source
    socket = assign(socket, :source_filter, source_filter)
    {:noreply, load_game_data(socket)}
  end

  @impl true
  def handle_event("toggle_legacy", _params, socket) do
    show_legacy = !socket.assigns.show_legacy
    socket = assign(socket, :show_legacy, show_legacy)
    {:noreply, load_game_data(socket)}
  end

  @impl true
  def handle_event("create_character", _params, socket) do
    if socket.assigns.character.name == "" do
      {:noreply, put_flash(socket, :error, "Please enter a character name")}
    else
      {:noreply, assign(socket, :saving, true)}

      attrs = build_character_attrs(socket.assigns.character)

      case Characters.create_character(attrs) do
        {:ok, character} ->
          {:noreply,
           socket
           |> put_flash(:info, "Character created successfully!")
           |> redirect(to: "/characters/#{character.id}")}

        {:error, reason} ->
          {:noreply,
           socket
           |> assign(:saving, false)
           |> put_flash(:error, "Failed to create character: #{inspect(reason)}")}
      end
    end
  end

  defp build_character_attrs(character) do
    base_scores = character.base_scores
    final_scores = if character.race do
      RulesEngine.apply_race_bonuses(base_scores, character.race)
    else
      base_scores
    end

    %{
      name: character.name,
      race: character.race,
      class: character.class,
      background: character.background,
      str: final_scores.str,
      dex: final_scores.dex,
      con: final_scores.con,
      int: final_scores.int,
      wis: final_scores.wis,
      cha: final_scores.cha
    }
  end

  defp calculate_preview(character) do
    base_scores = character.base_scores
    final_scores = if character.race do
      RulesEngine.apply_race_bonuses(base_scores, character.race)
    else
      base_scores
    end

    modifiers = %{
      str_mod: Characters.ability_modifier(final_scores.str),
      dex_mod: Characters.ability_modifier(final_scores.dex),
      con_mod: Characters.ability_modifier(final_scores.con),
      int_mod: Characters.ability_modifier(final_scores.int),
      wis_mod: Characters.ability_modifier(final_scores.wis),
      cha_mod: Characters.ability_modifier(final_scores.cha)
    }

    con_mod = modifiers.con_mod
    dex_mod = modifiers.dex_mod

    hp = if character.class do
      Characters.calculate_starting_hp(character.class, con_mod, 1)
    else
      nil
    end

    ac = Characters.calculate_ac(dex_mod)
    prof_bonus = Characters.proficiency_bonus(1)

    %{
      final_scores: final_scores,
      modifiers: modifiers,
      hp: hp,
      ac: ac,
      proficiency_bonus: prof_bonus
    }
  end

  @impl true
  def render(assigns) do
    preview = calculate_preview(assigns.character)
    remaining_points = case assigns.character.ability_method do
      :point_buy -> PointBuy.remaining_points(assigns.character.base_scores)
      _ -> nil
    end

    assigns = assign(assigns, :preview, preview)
    assigns = assign(assigns, :remaining_points, remaining_points)
    assigns = assign(assigns, :can_proceed, can_proceed?(assigns))

    ~H"""
    <div class="min-h-screen bg-sand-50">
      <div class="flex flex-col lg:flex-row">
        <!-- Left Column: Sculpting Area (65%) -->
        <div class="w-full lg:w-[65%] overflow-y-auto">
          <div class="max-w-4xl mx-auto px-6 lg:px-12 py-8 lg:py-16">
            <%= render_view(assigns) %>
          </div>
        </div>

        <!-- Right Column: Passport (35%) -->
        <div class="w-full lg:w-[35%] lg:sticky lg:top-0 lg:h-screen overflow-y-auto bg-sand-100">
          <div class="p-6 lg:p-8">
            <NordicComponents.passport_panel
              character={@character}
              preview={@preview}
            />
          </div>
        </div>
      </div>

      <!-- Continue Button -->
      <NordicComponents.continue_button
        show={@can_proceed}
        phx-click="next_step"
        disabled={!@can_proceed}
      />

      <!-- Class Details Slide-over -->
      <%= if @show_class_details && @selected_class do %>
        <div
          class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-end animate-fade-in"
          phx-click="hide_class_details"
        >
          <div
            class="w-full lg:w-1/2 h-full bg-sand-50 shadow-soft overflow-y-auto animate-slide-in"
            phx-click-away="hide_class_details"
          >
            <div class="p-8">
              <button
                phx-click="hide_class_details"
                class="mb-6 text-ink-500 hover:text-ink-900 transition-colors"
              >
                ← Close
              </button>
              <%= render_class_details(assigns) %>
            </div>
          </div>
        </div>
      <% end %>

      <!-- Tooltip -->
      <%= if @tooltip do %>
        <div class="fixed z-50 bg-ink-900 text-white px-4 py-2 rounded shadow-soft">
          <%= @tooltip.name %> (<%= @tooltip.type %>)
        </div>
      <% end %>
    </div>
    """
  end

  defp render_view(assigns) do
    case assigns.step do
      :origin -> render_origin_view(assigns)
      :path -> render_path_view(assigns)
      :constitution -> render_constitution_view(assigns)
      :inventory -> render_inventory_view(assigns)
      _ -> ~H"<div>Unknown step</div>"
    end
  end

  defp render_origin_view(assigns) do
    ~H"""
    <div>
      <h1 class="font-serif text-5xl font-semibold text-ink-900 mb-12">
        Let's begin. Who are you?
      </h1>

      <div class="mb-16">
              <NordicComponents.focus_input
                id="character_name"
                name="name"
                value={@character.name || ""}
                label="Character Name"
                size="4xl"
                phx-blur="update_name"
              />
      </div>

      <div class="mb-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="font-serif text-2xl font-semibold text-ink-900">Choose Your Race</h2>
          <div class="flex items-center gap-4">
            <select
              phx-change="filter_source"
              class="px-4 py-2 bg-transparent border-b-2 border-stone-300 text-ink-900 focus:border-forest-600 focus:outline-none"
            >
              <option value="">All Sources</option>
              <option value="PHB">Player's Handbook</option>
              <option value="XGE">Xanathar's Guide</option>
              <option value="TCE">Tasha's Cauldron</option>
            </select>
            <div class="flex items-center gap-2">
              <span class="text-sm text-ink-500">Legacy</span>
              <NordicComponents.toggle_pill
                id="legacy_toggle"
                checked={@show_legacy}
                phx-click="toggle_legacy"
              />
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 lg:gap-4">
          <%= for race <- @races do %>
            <div>
              <div
                phx-click="select_race"
                phx-value-race_name={race.name}
              >
                <NordicComponents.ghost_card
                  selected={@character.race == race.name}
                  class="text-center"
                >
                  <div class="mb-3 text-4xl">
                    <%= race_icon(race.name) %>
                  </div>
                  <div class="font-medium"><%= race.name %></div>
                </NordicComponents.ghost_card>
              </div>

              <%= if @expanded_race == race.name do %>
                <div class="mt-4 p-4 bg-sand-100 rounded-xl text-sm text-ink-700 leading-relaxed">
                  <%= if race.ability_bonuses do %>
                    <p class="mb-2">
                      <strong>Ability Bonuses:</strong> <%= format_ability_bonuses(race.ability_bonuses) %>
                    </p>
                  <% end %>
                  <p>Select this race to learn more about its traits and features.</p>
                </div>
              <% end %>
            </div>
          <% end %>
        </div>
      </div>
    </div>
    """
  end

  defp render_path_view(assigns) do
    ~H"""
    <div>
      <h1 class="font-serif text-5xl font-semibold text-ink-900 mb-12">The Path</h1>

      <div class="mb-12">
        <h2 class="font-serif text-2xl font-semibold text-ink-900 mb-6">Choose Your Class</h2>
        <div class="space-y-3">
          <%= for class <- @classes do %>
            <div
              class={[
                "flex items-center justify-between p-6 rounded-xl transition-all duration-300 cursor-pointer",
                "bg-sand-50 hover:bg-sand-100 hover:translate-x-2",
                if(@character.class == class.name, do: "bg-forest-600 text-white")
              ]}
              phx-click="select_class"
              phx-value-class_name={class.name}
            >
              <div class="font-semibold text-xl"><%= class.name %></div>
              <div class="text-lg">d<%= class.hit_die %></div>
            </div>
          <% end %>
        </div>
      </div>

      <div class="mb-12">
        <h2 class="font-serif text-2xl font-semibold text-ink-900 mb-6">Choose Your Background</h2>
        <div class="grid grid-cols-2 gap-4">
          <%= for bg <- @backgrounds do %>
            <NordicComponents.ghost_card
              selected={@character.background == bg}
              phx-click="select_background"
              phx-value-background={bg}
            >
              <%= bg %>
            </NordicComponents.ghost_card>
          <% end %>
        </div>
      </div>
    </div>
    """
  end

  defp render_constitution_view(assigns) do
    ~H"""
    <div>
      <h1 class="font-serif text-5xl font-semibold text-ink-900 mb-12">The Constitution</h1>

      <div class="mb-8">
        <label class="block text-sm font-medium text-ink-500 mb-3">Generation Method</label>
        <select
          phx-change="set_ability_method"
          name="method"
          class="w-full px-4 py-2 bg-transparent border-b-2 border-stone-300 text-ink-900 focus:border-forest-600 focus:outline-none"
        >
          <option value="point_buy" selected={@character.ability_method == :point_buy}>
            Point Buy (27 points)
          </option>
          <option value="standard_array" selected={@character.ability_method == :standard_array}>
            Standard Array
          </option>
          <option value="manual" selected={@character.ability_method == :manual}>
            Manual/Rolled
          </option>
        </select>
      </div>

      <%= if @character.ability_method == :point_buy do %>
        <div class="mb-8 p-6 bg-sand-100 rounded-xl">
          <div class="text-sm text-ink-500 mb-2">Points Remaining</div>
          <div class={[
            "text-3xl font-bold",
            cond do
              @remaining_points < 0 -> "text-clay-500"
              @remaining_points < 5 -> "text-clay-500"
              @remaining_points < 10 -> "text-ink-900"
              true -> "text-forest-600"
            end
          ]}>
            <%= @remaining_points || 0 %>
          </div>
          <div class="text-sm text-ink-500 mt-1">/ <%= PointBuy.default_budget() %></div>
        </div>
      <% end %>

      <div class="grid grid-cols-3 md:grid-cols-6 gap-4 md:gap-8">
        <%= for ability <- [:str, :dex, :con, :int, :wis, :cha] do %>
          <NordicComponents.stat_slider
            ability={ability}
            score={Map.get(@character.base_scores, ability, 8)}
            modifier={Map.get(@preview.modifiers, :"#{ability}_mod", 0)}
            phx_change="update_ability_score"
          />
        <% end %>
      </div>
    </div>
    """
  end

  defp render_inventory_view(assigns) do
    ~H"""
    <div>
      <h1 class="font-serif text-5xl font-semibold text-ink-900 mb-12">The Inventory</h1>

      <div class="space-y-2">
        <%= for item <- ["Longsword", "Shield", "Chain Mail", "Explorer's Pack"] do %>
          <div class="flex items-center gap-3 py-3">
            <input
              type="checkbox"
              checked={item in (@character.equipment || [])}
              phx-click="toggle_equipment"
              phx-value-item_name={item}
              class="w-5 h-5 rounded border-stone-300 text-forest-600 focus:ring-forest-600"
            />
            <label class={[
              "text-lg cursor-pointer",
              if(item in (@character.equipment || []), do: "line-through text-ink-500", else: "text-ink-900")
            ]}>
              <%= item %>
            </label>
          </div>
        <% end %>
      </div>

      <div class="mt-12">
        <button
          phx-click="create_character"
          disabled={@saving || @character.name == ""}
          class={[
            "w-full py-4 bg-forest-600 text-white rounded-xl shadow-soft",
            "font-medium text-lg transition-all duration-300",
            "hover:bg-forest-700 hover:shadow-lg",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          ]}
        >
          <%= if @saving, do: "Creating...", else: "Create Character" %>
        </button>
      </div>
    </div>
    """
  end

  defp render_class_details(assigns) do
    selected_class = Enum.find(assigns.classes, &(&1.name == assigns.selected_class))
    if selected_class do
      ~H"""
      <div>
        <h2 class="font-serif text-3xl font-semibold text-ink-900 mb-6"><%= selected_class.name %></h2>
        <div class="space-y-4 text-ink-700">
          <div>
            <strong>Hit Die:</strong> d<%= selected_class.hit_die %>
          </div>
          <div>
            <strong>Primary Ability:</strong> <%= String.capitalize(to_string(selected_class.primary_ability || :str)) %>
          </div>
        </div>
      </div>
      """
    else
      ~H"<div>Class details not available</div>"
    end
  end

  defp race_icon(race_name) do
    # Simple icon placeholders - in production, use actual SVG icons
    icon_map = %{
      "Human" => "👤",
      "Elf" => "🌿",
      "Dwarf" => "⛰️",
      "Halfling" => "🍃",
      "Dragonborn" => "🐉",
      "Gnome" => "🔧",
      "Half-Elf" => "🌙",
      "Half-Orc" => "⚔️",
      "Tiefling" => "🔥"
    }
    Map.get(icon_map, race_name, "⚪")
  end

  defp get_racial_bonus(race_name, ability) when is_binary(race_name) do
    case Characters.get_race(race_name) do
      %{ability_bonuses: bonuses} when is_map(bonuses) ->
        Map.get(bonuses, ability, 0)
      _ -> 0
    end
  end

  defp get_racial_bonus(_, _), do: 0

  defp format_ability_bonuses(bonuses) when is_map(bonuses) do
    bonuses
    |> Enum.filter(fn {_k, v} -> v > 0 end)
    |> Enum.map(fn {k, v} -> "#{String.upcase(to_string(k))} +#{v}" end)
    |> Enum.join(", ")
  end

  defp format_ability_bonuses(_), do: ""
end
