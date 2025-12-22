defmodule DndAppWeb.Router do
  use DndAppWeb, :router

  import Phoenix.LiveView.Router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: {DndAppWeb.Layouts, :root}
    plug :protect_from_forgery
    plug :put_secure_browser_headers
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", DndAppWeb do
    pipe_through :api

    get "/health", HealthController, :check
  end

  scope "/", DndAppWeb do
    pipe_through :browser

    live "/", HomeLive, :index
    live "/characters/new/method", MethodSelectionLive, :index
    live "/characters/premade", PremadeLive, :index
    live "/characters", CharacterLive.Index, :index
    live "/characters/new", CharacterLive.New, :new
    live "/characters/:id", CharacterLive.Show, :show
  end
end
