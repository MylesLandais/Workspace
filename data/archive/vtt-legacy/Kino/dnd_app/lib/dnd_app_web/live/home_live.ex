defmodule DndAppWeb.HomeLive do
  use DndAppWeb, :live_view
  alias DndApp.Dice

  @impl true
  def mount(_params, _session, socket) do
    {:ok,
     socket
     |> assign(:dice_expression, "1d20")
     |> assign(:dice_result, nil)
     |> assign(:error, nil)}
  end

  @impl true
  def handle_event("roll_dice", %{"expression" => expression}, socket) do
    case Dice.roll(expression) do
      {:ok, result} ->
        {:noreply,
         socket
         |> assign(:dice_result, result)
         |> assign(:error, nil)}

      {:error, message} ->
        {:noreply,
         socket
         |> assign(:dice_result, nil)
         |> assign(:error, message)}
    end
  end

  @impl true
  def handle_event("quick_roll", %{"expression" => expression}, socket) do
    case Dice.roll(expression) do
      {:ok, result} ->
        {:noreply,
         socket
         |> assign(:dice_expression, expression)
         |> assign(:dice_result, result)
         |> assign(:error, nil)}

      {:error, message} ->
        {:noreply,
         socket
         |> assign(:dice_result, nil)
         |> assign(:error, message)}
    end
  end

  @impl true
  def render(assigns) do
    ~H"""
    <div class="container">
      <h1>D&D 5e Dice Roller</h1>

      <div class="dice-roller">
        <h2>Roll Dice</h2>

        <form phx-submit="roll_dice">
          <div class="form-group">
            <label for="expression">Dice Expression</label>
            <input
              type="text"
              id="expression"
              name="expression"
              value={@dice_expression}
              placeholder="e.g., 1d20, 4d6dl1, 2d8+3"
              class="form-input"
            />
            <small>Examples: 1d20, 4d6dl1 (drop lowest), 2d8+3, 1d20+5</small>
          </div>

          <button type="submit" class="btn btn-primary">Roll</button>
        </form>

        <div class="quick-rolls">
          <h3>Quick Rolls</h3>
          <div class="quick-roll-buttons">
            <button phx-click="quick_roll" phx-value-expression="1d20" class="btn btn-secondary">d20</button>
            <button phx-click="quick_roll" phx-value-expression="1d12" class="btn btn-secondary">d12</button>
            <button phx-click="quick_roll" phx-value-expression="1d10" class="btn btn-secondary">d10</button>
            <button phx-click="quick_roll" phx-value-expression="1d8" class="btn btn-secondary">d8</button>
            <button phx-click="quick_roll" phx-value-expression="1d6" class="btn btn-secondary">d6</button>
            <button phx-click="quick_roll" phx-value-expression="1d4" class="btn btn-secondary">d4</button>
            <button phx-click="quick_roll" phx-value-expression="4d6dl1" class="btn btn-secondary">4d6 (ability)</button>
          </div>
        </div>

        <%= if @error do %>
          <div class="alert alert-error">
            <strong>Error:</strong> <%= @error %>
          </div>
        <% end %>

        <%= if @dice_result do %>
          <div class="dice-result">
            <h3>Result: <%= @dice_result.total %></h3>
            <div class="result-details">
              <p><strong>Expression:</strong> <%= @dice_result.expression %></p>
              <p><strong>Rolls:</strong> <%= Enum.join(@dice_result.rolls, ", ") %></p>
              <%= if length(@dice_result.dropped) > 0 do %>
                <p><strong>Dropped:</strong> <%= Enum.join(@dice_result.dropped, ", ") %></p>
              <% end %>
              <%= if @dice_result.modifier != 0 do %>
                <p><strong>Modifier:</strong> <%= if @dice_result.modifier > 0, do: "+", else: "" %><%= @dice_result.modifier %></p>
              <% end %>
              <p><strong>Total:</strong> <span class="total"><%= @dice_result.total %></span></p>
            </div>
          </div>
        <% end %>
      </div>

      <div class="navigation">
        <a href="/characters/new/method" class="btn btn-primary">Create New Character</a>
        <a href="/characters" class="btn btn-secondary">View Characters</a>
      </div>
    </div>
    """
  end
end
