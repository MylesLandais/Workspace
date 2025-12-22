defmodule DndAppWeb.Layouts do
  use DndAppWeb, :html
  import Phoenix.Controller, only: [get_csrf_token: 0]
  import Phoenix.LiveView, only: [live_flash: 2]

  def app(assigns) do
    ~H"""
    <div class="container">
      <p class="alert alert-info" role="alert"
        phx-click="lv:clear-flash"
        phx-value-key="info"><%= live_flash(@flash, :info) %></p>
      <p class="alert alert-danger" role="alert"
        phx-click="lv:clear-flash"
        phx-value-key="error"><%= live_flash(@flash, :error) %></p>
      <%= @inner_content %>
    </div>
    """
  end

  def root(assigns) do
    ~H"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="csrf-token" content={get_csrf_token()} />
        <.live_title suffix=" · D&D App">
          <%= assigns[:page_title] || "D&D 5e Character Creator" %>
        </.live_title>
        <link phx-track-static rel="stylesheet" href="/assets/app.css" />
        <script defer phx-track-static type="text/javascript" src="/assets/app.js"></script>
      </head>
      <body>
        <header>
          <section class="container">
            <nav>
              <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/characters">Characters</a></li>
                <li><a href="/characters/new">New Character</a></li>
              </ul>
            </nav>
          </section>
        </header>
        <main>
          <%= @inner_content %>
        </main>
      </body>
    </html>
    """
  end
end
