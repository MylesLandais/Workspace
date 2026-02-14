defmodule DndAppWeb.PremadeLive do
  use DndAppWeb, :live_view
  alias DndApp.Characters
  alias DndApp.DB.Neo4j

  @impl true
  def mount(_params, _session, socket) do
    {:ok,
     socket
     |> assign(:templates, [])
     |> load_templates()}
  end

  defp load_templates(socket) do
    # For now, return empty list
    # In the future, query Neo4j for :CharacterTemplate nodes
    templates = []
    assign(socket, :templates, templates)
  end

  @impl true
  def handle_event("load_template", %{"template_id" => template_id}, socket) do
    # Load template and redirect to character creation
    {:noreply, redirect(socket, to: "/characters/new?template=#{template_id}")}
  end

  @impl true
  def render(assigns) do
    ~H"""
    <div class="container mx-auto px-4 py-8">
      <h1 class="text-4xl font-bold mb-8">Premade Character Templates</h1>

      <%= if length(@templates) == 0 do %>
        <div class="bg-white rounded-lg shadow-md p-8 text-center">
          <p class="text-gray-600 mb-4">No premade templates available yet.</p>
          <p class="text-sm text-gray-500">
            Premade templates will be available in a future update.
          </p>
          <a href="/characters/new" class="mt-4 inline-block text-blue-600 hover:text-blue-800">
            Create a new character instead →
          </a>
        </div>
      <% else %>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <%= for template <- @templates do %>
            <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-shadow">
              <h3 class="text-xl font-semibold mb-2"><%= template.name %></h3>
              <p class="text-sm text-gray-600 mb-4"><%= template.description %></p>
              <button
                phx-click="load_template"
                phx-value-template_id={template.id}
                class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
              >
                Use Template
              </button>
            </div>
          <% end %>
        </div>
      <% end %>
    </div>
    """
  end
end
