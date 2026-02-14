defmodule DndAppWeb.MethodSelectionLive do
  use DndAppWeb, :live_view

  @impl true
  def mount(_params, _session, socket) do
    {:ok,
     socket
     |> assign(:beginner_mode, false)}
  end

  @impl true
  def handle_event("toggle_beginner", _params, socket) do
    {:noreply, assign(socket, :beginner_mode, !socket.assigns.beginner_mode)}
  end

  @impl true
  def handle_event("select_mode", %{"mode" => mode}, socket) do
    mode_atom = String.to_atom(mode)
    path = "/characters/new?mode=#{mode}#{if socket.assigns.beginner_mode && mode == "standard", do: "&beginner=true", else: ""}"
    {:noreply, redirect(socket, to: path)}
  end

  @impl true
  def render(assigns) do
    ~H"""
    <div class="container mx-auto px-4 py-8">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold mb-4">Create Your Character</h1>
        <p class="text-lg text-gray-600">Choose how you'd like to build your D&D 5e character</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
        <!-- Standard Mode -->
        <div class="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-semibold">Standard</h2>
            <span class="text-sm text-gray-500">Full Control</span>
          </div>
          <p class="text-gray-600 mb-4">
            Step-by-step full customization with all options available.
          </p>
          <div class="mb-4">
            <label class="flex items-center">
              <input
                type="checkbox"
                checked={@beginner_mode}
                phx-click="toggle_beginner"
                class="mr-2"
              />
              <span class="text-sm">Beginner? (Enables tooltips and guided help)</span>
            </label>
          </div>
          <button
            phx-click="select_mode"
            phx-value-mode="standard"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors"
          >
            Start Building
          </button>
        </div>

        <!-- Quick Build Mode -->
        <div class="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-semibold">Quick Build</h2>
            <span class="text-sm text-gray-500">Fast</span>
          </div>
          <p class="text-gray-600 mb-4">
            Minimal input - just select Species and Class, we'll handle the rest.
          </p>
          <button
            phx-click="select_mode"
            phx-value-mode="quick"
            class="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition-colors"
          >
            Start Building
          </button>
        </div>

        <!-- Random Mode -->
        <div class="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-semibold">Random</h2>
            <span class="text-sm text-gray-500">Surprise Me</span>
          </div>
          <p class="text-gray-600 mb-4">
            Procedurally generated character based on optional parameters.
          </p>
          <button
            phx-click="select_mode"
            phx-value-mode="random"
            class="w-full bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 transition-colors"
          >
            Start Building
          </button>
        </div>

        <!-- Premade Mode -->
        <div class="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-semibold">Premade</h2>
            <span class="text-sm text-gray-500">Templates</span>
          </div>
          <p class="text-gray-600 mb-4">
            Browse ready-to-play character templates and customize as needed.
          </p>
          <button
            phx-click="select_mode"
            phx-value-mode="premade"
            class="w-full bg-orange-600 text-white py-2 px-4 rounded hover:bg-orange-700 transition-colors"
          >
            Start Browsing
          </button>
        </div>
      </div>
    </div>
    """
  end
end
