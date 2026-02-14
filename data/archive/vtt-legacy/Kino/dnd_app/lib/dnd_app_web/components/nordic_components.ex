defmodule DndAppWeb.NordicComponents do
  @moduledoc """
  Nordic Atlas design system components.
  Scandinavian minimalism with clean lines, negative space, and natural textures.
  """
  use Phoenix.Component

  @doc """
  Focus Input - Underlined input with floating label animation.
  """
  attr :id, :string, required: true
  attr :name, :string, required: true
  attr :value, :string, default: ""
  attr :placeholder, :string, default: ""
  attr :label, :string, required: true
  attr :size, :string, default: "base", values: ["base", "xl", "4xl"]
  attr :phx_debounce, :string, default: "300"
  attr :phx_blur, :string, default: "update_field"
  attr :class, :string, default: ""

  def focus_input(assigns) do
    size_classes = case assigns.size do
      "4xl" -> "text-4xl"
      "xl" -> "text-xl"
      _ -> "text-base"
    end

    has_value = assigns.value != "" && assigns.value != nil

    ~H"""
    <div class={["group relative", @class]}>
      <input
        type="text"
        id={@id}
        name={@name}
        value={@value}
        phx-debounce={@phx_debounce}
        phx-blur={@phx_blur}
        class={[
          "block w-full border-0 border-b-2 border-stone-300 bg-transparent px-0 py-2",
          "focus:border-forest-600 focus:ring-0 transition-colors outline-none",
          "placeholder:text-transparent",
          size_classes
        ]}
        placeholder=" "
      />
      <label
        for={@id}
        class={[
          "absolute top-2 left-0 origin-[0] duration-300 pointer-events-none transition-all",
          if(has_value || @value != "",
            do: "-translate-y-6 scale-75 text-ink-500",
            else: "text-ink-500 group-focus-within:-translate-y-6 group-focus-within:scale-75"
          )
        ]}
      >
        <%= @label %>
      </label>
    </div>
    """
  end

  @doc """
  Ghost Card - Selectable card with no borders, background shift on hover/select.
  """
  attr :id, :string, default: nil
  attr :selected, :boolean, default: false
  attr :phx_click, :string, default: nil
  attr :phx_value, :map, default: %{}
  attr :class, :string, default: ""

  slot :inner_block, required: true

  def ghost_card(assigns) do
    base_classes = [
      "p-6 rounded-xl transition-all duration-300 cursor-pointer",
      "border-0",
      if(assigns.selected,
        do: "bg-forest-600 text-white shadow-soft",
        else: "bg-sand-50 hover:bg-sand-100 text-ink-900"
      )
    ]

    click_attrs = if assigns.phx_click do
      [
        {"phx-click", assigns.phx_click}
        | Enum.map(assigns.phx_value, fn {k, v} -> {"phx-value-#{k}", v} end)
      ]
    else
      []
    end

    assigns = assign(assigns, :base_classes, base_classes)
    assigns = assign(assigns, :click_attrs, click_attrs)

    ~H"""
    <div
      id={@id}
      class={[@base_classes, @class]}
      {click_attrs}
    >
      <%= render_slot(@inner_block) %>
    </div>
    """
  end

  @doc """
  Toggle Pill - Binary choice toggle with smooth sliding animation.
  """
  attr :id, :string, required: true
  attr :checked, :boolean, default: false
  attr :label, :string, default: ""
  attr :phx_click, :string, default: "toggle"
  attr :phx_value, :map, default: %{}

  def toggle_pill(assigns) do
    ~H"""
    <button
      id={@id}
      type="button"
      phx-click={@phx_click}
      {Enum.map(@phx_value, fn {k, v} -> {"phx-value-#{k}", v} end)}
      class={[
        "relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-300",
        if(@checked, do: "bg-forest-600", else: "bg-stone-300")
      ]}
    >
      <span
        class={[
          "inline-block h-6 w-6 transform rounded-full bg-white shadow-soft transition-transform duration-300",
          if(@checked, do: "translate-x-7", else: "translate-x-1")
        ]}
      />
    </button>
    """
  end

  @doc """
  Stat Slider - Vertical bar for ability score adjustment with drag handle.
  """
  attr :ability, :atom, required: true
  attr :score, :integer, required: true
  attr :modifier, :integer, required: true
  attr :min, :integer, default: 8
  attr :max, :integer, default: 15
  attr :disabled, :boolean, default: false
  attr :phx_change, :string, default: "update_ability_score"

  def stat_slider(assigns) do
    ability_str = String.upcase(to_string(assigns.ability))
    percentage = ((assigns.score - assigns.min) / (assigns.max - assigns.min)) * 100
    modifier_display = if assigns.modifier >= 0, do: "+#{assigns.modifier}", else: "#{assigns.modifier}"

    ~H"""
    <div class="flex flex-col items-center space-y-2">
      <div class="text-sm font-medium text-ink-500"><%= ability_str %></div>
      <div class="relative w-16 h-64 bg-sand-100 rounded-xl overflow-hidden">
        <div
          class={[
            "absolute bottom-0 w-full bg-forest-600 transition-all duration-300",
            if(assigns.disabled, do: "opacity-50")
          ]}
          style={"height: #{percentage}%"}
        />
        <input
          type="range"
          min={@min}
          max={@max}
          value={@score}
          disabled={@disabled}
          phx-change={@phx_change}
          phx-value-ability={@ability}
          class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        />
      </div>
      <div class="text-center">
        <div class="text-3xl font-bold text-ink-900"><%= modifier_display %></div>
        <div class="text-sm text-ink-500"><%= assigns.score %></div>
      </div>
    </div>
    """
  end

  @doc """
  Continue Button - Fixed position button that fades in when ready.
  """
  attr :show, :boolean, default: false
  attr :label, :string, default: "Continue"
  attr :phx_click, :string, default: "next_step"
  attr :disabled, :boolean, default: false

  def continue_button(assigns) do
    ~H"""
    <%= if @show do %>
      <div
        class={[
          "fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50",
          "transition-opacity duration-500",
          if(@show, do: "opacity-100", else: "opacity-0 pointer-events-none")
        ]}
      >
        <button
          type="button"
          phx-click={@phx_click}
          disabled={@disabled}
          class={[
            "px-8 py-4 bg-forest-600 text-white rounded-xl shadow-soft",
            "font-medium text-lg transition-all duration-300",
            "hover:bg-forest-700 hover:shadow-lg",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          ]}
        >
          <%= @label %>
        </button>
      </div>
    <% end %>
    """
  end

  @doc """
  Passport Panel - Minimalist character summary for the right sidebar.
  """
  attr :character, :map, required: true
  attr :preview, :map, default: %{}

  def passport_panel(assigns) do
    ~H"""
    <div class="bg-sand-100 rounded-xl p-6 sticky top-4 shadow-soft">
      <h3 class="font-serif text-xl font-semibold text-ink-900 mb-6">Passport</h3>

      <%= if @character.name && @character.name != "" do %>
        <div class="mb-6">
          <div class="text-2xl font-serif font-bold text-ink-900"><%= @character.name %></div>
        </div>
      <% else %>
        <div class="mb-6 text-ink-500 italic">Unnamed Character</div>
      <% end %>

      <div class="space-y-4 mb-6">
        <%= if @character.race do %>
          <div>
            <span class="text-sm text-ink-500">Race</span>
            <div class="text-base font-medium text-ink-900"><%= @character.race %></div>
          </div>
        <% end %>
        <%= if @character.class do %>
          <div>
            <span class="text-sm text-ink-500">Class</span>
            <div class="text-base font-medium text-ink-900"><%= @character.class %></div>
          </div>
        <% end %>
        <%= if @character.background do %>
          <div>
            <span class="text-sm text-ink-500">Background</span>
            <div class="text-base font-medium text-ink-900"><%= @character.background %></div>
          </div>
        <% end %>
      </div>

      <%= if @preview.final_scores do %>
        <div class="mb-6">
          <h4 class="text-sm font-medium text-ink-500 mb-3">Ability Scores</h4>
          <div class="grid grid-cols-3 gap-3">
            <%= for ability <- [:str, :dex, :con, :int, :wis, :cha] do %>
              <div class="text-center">
                <div class="text-xs text-ink-500 mb-1"><%= String.upcase(to_string(ability)) %></div>
                <%= if score = Map.get(@preview.final_scores, ability) do %>
                  <div class="text-lg font-semibold text-ink-900"><%= score %></div>
                  <%= if mod = Map.get(@preview.modifiers, :"#{ability}_mod") do %>
                    <div class="text-xs text-ink-500">
                      <%= if mod >= 0, do: "+", else: "" %><%= mod %>
                    </div>
                  <% end %>
                <% end %>
              </div>
            <% end %>
          </div>
        </div>
      <% end %>

      <%= if @preview.hp && @preview.ac do %>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <div class="text-xs text-ink-500 mb-1">AC</div>
            <div class="text-lg font-semibold text-ink-900"><%= @preview.ac %></div>
          </div>
          <div>
            <div class="text-xs text-ink-500 mb-1">HP</div>
            <div class="text-lg font-semibold text-ink-900"><%= @preview.hp %></div>
          </div>
          <div>
            <div class="text-xs text-ink-500 mb-1">Prof.</div>
            <div class="text-lg font-semibold text-ink-900">+<%= @preview.proficiency_bonus %></div>
          </div>
        </div>
      <% end %>
    </div>
    """
  end
end
