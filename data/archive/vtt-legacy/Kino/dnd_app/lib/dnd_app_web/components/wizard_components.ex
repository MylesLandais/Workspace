defmodule DndAppWeb.WizardComponents do
  @moduledoc """
  Reusable components for the character creation wizard.
  """
  use Phoenix.Component

  @doc """
  Breadcrumb navigation for wizard steps.
  """
  attr :current_step, :atom, required: true
  attr :steps, :list, required: true
  attr :on_click, :string, default: "goto_step"

  def breadcrumb(assigns) do
    ~H"""
    <nav class="flex items-center justify-center mb-6" aria-label="Wizard steps">
      <ol class="flex space-x-2">
        <%= for {step, index} <- Enum.with_index(@steps) do %>
          <li>
            <button
              phx-click={@on_click}
              phx-value-step={step}
              class={[
                "px-4 py-2 rounded transition-colors",
                if(@current_step == step,
                  do: "bg-blue-600 text-white font-semibold",
                  else: "bg-gray-200 text-gray-700 hover:bg-gray-300"
                )
              ]}
            >
              <%= index + 1 %>. <%= format_step_name(step) %>
            </button>
          </li>
        <% end %>
      </ol>
    </nav>
    """
  end

  defp format_step_name(:class), do: "Class"
  defp format_step_name(:background), do: "Background"
  defp format_step_name(:species), do: "Species"
  defp format_step_name(:abilities), do: "Abilities"
  defp format_step_name(:equipment), do: "Equipment"
  defp format_step_name(:review), do: "Review"
  defp format_step_name(step), do: to_string(step) |> String.capitalize()

  @doc """
  Character preview sidebar.
  """
  attr :character, :map, required: true
  attr :preview, :map, default: %{}

  def character_preview(assigns) do
    ~H"""
    <div class="bg-white rounded-lg shadow-md p-4 sticky top-4">
      <h3 class="text-xl font-semibold mb-4">Character Preview</h3>

      <%= if @character.name && @character.name != "" do %>
        <div class="mb-4">
          <div class="text-2xl font-bold"><%= @character.name %></div>
        </div>
      <% else %>
        <div class="mb-4 text-gray-400 italic">Unnamed Character</div>
      <% end %>

      <div class="space-y-2 mb-4">
        <%= if @character.race do %>
          <p><strong>Race:</strong> <%= @character.race %></p>
        <% end %>
        <%= if @character.class do %>
          <p><strong>Class:</strong> <%= @character.class %></p>
        <% end %>
        <%= if @character.background do %>
          <p><strong>Background:</strong> <%= @character.background %></p>
        <% end %>
      </div>

      <%= if @preview.final_scores do %>
        <div class="mb-4">
          <h4 class="font-semibold mb-2">Ability Scores</h4>
          <div class="grid grid-cols-3 gap-2 text-sm">
            <%= for ability <- [:str, :dex, :con, :int, :wis, :cha] do %>
              <div class="text-center">
                <div class="font-semibold"><%= String.upcase(to_string(ability)) %></div>
                <%= if score = Map.get(@preview.final_scores, ability) do %>
                  <div class="text-lg"><%= score %></div>
                  <%= if mod = Map.get(@preview.modifiers, :"#{ability}_mod") do %>
                    <div class="text-xs text-gray-600">
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
        <div class="grid grid-cols-3 gap-2 text-sm">
          <div>
            <div class="text-xs text-gray-600">AC</div>
            <div class="text-lg font-semibold"><%= @preview.ac %></div>
          </div>
          <div>
            <div class="text-xs text-gray-600">HP</div>
            <div class="text-lg font-semibold"><%= @preview.hp %></div>
          </div>
          <div>
            <div class="text-xs text-gray-600">Prof. Bonus</div>
            <div class="text-lg font-semibold">+<%= @preview.proficiency_bonus %></div>
          </div>
        </div>
      <% end %>
    </div>
    """
  end

  @doc """
  Step navigation buttons (Previous/Next).
  """
  attr :current_step, :atom, required: true
  attr :steps, :list, required: true
  attr :can_proceed, :boolean, default: true

  def step_navigation(assigns) do
    current_index = Enum.find_index(assigns.steps, &(&1 == assigns.current_step))
    has_prev = current_index > 0
    has_next = current_index < length(assigns.steps) - 1

    ~H"""
    <div class="flex justify-between mt-6">
      <button
        phx-click="prev_step"
        disabled={!has_prev}
        class={[
          "px-6 py-2 rounded transition-colors",
          if(has_prev,
            do: "bg-gray-600 text-white hover:bg-gray-700",
            else: "bg-gray-300 text-gray-500 cursor-not-allowed"
          )
        ]}
      >
        ← Previous
      </button>
      <button
        phx-click="next_step"
        disabled={!has_next || !@can_proceed}
        class={[
          "px-6 py-2 rounded transition-colors",
          if(has_next && @can_proceed,
            do: "bg-blue-600 text-white hover:bg-blue-700",
            else: "bg-gray-300 text-gray-500 cursor-not-allowed"
          )
        ]}
      >
        Next →
      </button>
    </div>
    """
  end

  @doc """
  Name suggestions component.
  """
  attr :race, :string, default: nil
  attr :suggestions, :list, default: []
  attr :on_select, :string, default: "select_name"

  def name_suggestions(assigns) do
    ~H"""
    <div class="mb-4">
      <button
        phx-click="suggest_names"
        phx-value-race={@race}
        class="text-sm text-blue-600 hover:text-blue-800 mb-2"
      >
        Get Name Suggestions
      </button>
      <%= if length(@suggestions) > 0 do %>
        <div class="flex flex-wrap gap-2">
          <%= for name <- @suggestions do %>
            <button
              phx-click={@on_select}
              phx-value-name={name}
              class="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
            >
              <%= name %>
            </button>
          <% end %>
        </div>
      <% end %>
    </div>
    """
  end
end
