defmodule DndAppWeb.CharacterLive.Show do
  use DndAppWeb, :live_view
  alias DndApp.Characters

  @impl true
  def mount(%{"id" => id}, _session, socket) do
    case Characters.get_character(id) do
      {:ok, character} ->
        {:ok, assign(socket, :character, character)}

      {:error, :not_found} ->
        {:ok,
         socket
         |> put_flash(:error, "Character not found")
         |> redirect(to: "/characters")}

      {:error, reason} ->
        {:ok,
         socket
         |> put_flash(:error, "Error loading character: #{inspect(reason)}")
         |> redirect(to: "/characters")}
    end
  end

  @impl true
  def handle_event("delete", _params, socket) do
    case Characters.delete_character(socket.assigns.character.id) do
      :ok ->
        {:noreply,
         socket
         |> put_flash(:info, "Character deleted")
         |> redirect(to: "/characters")}

      {:error, reason} ->
        {:noreply, put_flash(socket, :error, "Failed to delete: #{inspect(reason)}")}
    end
  end

  @impl true
  def render(assigns) do
    ~H"""
    <div class="container">
      <div class="character-header">
        <h1><%= @character.name %></h1>
        <div class="character-meta">
          <span><strong>Level <%= @character.level %></strong></span>
          <span><%= @character.race %></span>
          <span><%= @character.class %></span>
          <span><%= @character.background %></span>
        </div>
        <div class="character-actions">
          <a href="/characters" class="btn btn-secondary">Back to List</a>
          <button phx-click="delete" class="btn btn-danger">Delete</button>
        </div>
      </div>

      <div class="character-sheet">
        <div class="sheet-section">
          <h2>Ability Scores</h2>
          <div class="ability-scores-grid">
            <div class="ability-score">
              <div class="ability-label">STR</div>
              <div class="ability-value"><%= @character.str %></div>
              <div class="ability-modifier">
                <%= if @character.str_mod >= 0, do: "+", else: "" %><%= @character.str_mod %>
              </div>
            </div>
            <div class="ability-score">
              <div class="ability-label">DEX</div>
              <div class="ability-value"><%= @character.dex %></div>
              <div class="ability-modifier">
                <%= if @character.dex_mod >= 0, do: "+", else: "" %><%= @character.dex_mod %>
              </div>
            </div>
            <div class="ability-score">
              <div class="ability-label">CON</div>
              <div class="ability-value"><%= @character.con %></div>
              <div class="ability-modifier">
                <%= if @character.con_mod >= 0, do: "+", else: "" %><%= @character.con_mod %>
              </div>
            </div>
            <div class="ability-score">
              <div class="ability-label">INT</div>
              <div class="ability-value"><%= @character.int %></div>
              <div class="ability-modifier">
                <%= if @character.int_mod >= 0, do: "+", else: "" %><%= @character.int_mod %>
              </div>
            </div>
            <div class="ability-score">
              <div class="ability-label">WIS</div>
              <div class="ability-value"><%= @character.wis %></div>
              <div class="ability-modifier">
                <%= if @character.wis_mod >= 0, do: "+", else: "" %><%= @character.wis_mod %>
              </div>
            </div>
            <div class="ability-score">
              <div class="ability-label">CHA</div>
              <div class="ability-value"><%= @character.cha %></div>
              <div class="ability-modifier">
                <%= if @character.cha_mod >= 0, do: "+", else: "" %><%= @character.cha_mod %>
              </div>
            </div>
          </div>
        </div>

        <div class="sheet-section">
          <h2>Combat Stats</h2>
          <div class="combat-stats">
            <div class="stat-item">
              <label>Armor Class (AC)</label>
              <div class="stat-value"><%= @character.ac %></div>
            </div>
            <div class="stat-item">
              <label>Hit Points</label>
              <div class="stat-value"><%= @character.current_hp %> / <%= @character.max_hp %></div>
            </div>
            <div class="stat-item">
              <label>Proficiency Bonus</label>
              <div class="stat-value">
                <%= if @character.proficiency_bonus >= 0, do: "+", else: "" %><%= @character.proficiency_bonus %>
              </div>
            </div>
          </div>
        </div>

        <div class="sheet-section">
          <h2>Character Information</h2>
          <div class="info-grid">
            <div class="info-item">
              <label>Race</label>
              <div><%= @character.race %></div>
            </div>
            <div class="info-item">
              <label>Class</label>
              <div><%= @character.class %></div>
            </div>
            <div class="info-item">
              <label>Background</label>
              <div><%= @character.background %></div>
            </div>
            <div class="info-item">
              <label>Level</label>
              <div><%= @character.level %></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """
  end
end
