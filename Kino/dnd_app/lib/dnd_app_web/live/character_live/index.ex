defmodule DndAppWeb.CharacterLive.Index do
  use DndAppWeb, :live_view
  alias DndApp.Characters

  @impl true
  def mount(_params, _session, socket) do
    case Characters.list_characters() do
      {:ok, characters} ->
        {:ok, assign(socket, :characters, characters)}

      {:error, reason} ->
        {:ok,
         socket
         |> assign(:characters, [])
         |> put_flash(:error, "Error loading characters: #{inspect(reason)}")}
    end
  end

  @impl true
  def render(assigns) do
    ~H"""
    <div class="container">
      <div class="characters-header">
        <h1>Characters</h1>
        <a href="/characters/new" class="btn btn-primary">Create New Character</a>
      </div>

      <%= if length(@characters) == 0 do %>
        <div class="empty-state">
          <p>No characters yet. Create your first character to get started!</p>
          <a href="/characters/new" class="btn btn-primary">Create Character</a>
        </div>
      <% else %>
        <div class="characters-list">
          <%= for character <- @characters do %>
            <div class="character-card">
              <div class="character-card-header">
                <h3><%= character.name %></h3>
                <span class="character-level">Level <%= character.level %></span>
              </div>
              <div class="character-card-body">
                <p><strong>Race:</strong> <%= character.race %></p>
                <p><strong>Class:</strong> <%= character.class %></p>
              </div>
              <div class="character-card-actions">
                <a href={"/characters/#{character.id}"} class="btn btn-primary">View</a>
              </div>
            </div>
          <% end %>
        </div>
      <% end %>
    </div>
    """
  end
end
