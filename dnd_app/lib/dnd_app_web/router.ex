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

  pipeline :graphql do
    plug Absinthe.Plug, schema: DndAppWeb.GraphQL.Schema
  end

  scope "/", DndAppWeb do
    pipe_through :api

    get "/health", HealthController, :check
  end

  scope "/api" do
    pipe_through :graphql

    forward "/graphql", Absinthe.Plug, schema: DndAppWeb.GraphQL.Schema

    forward "/graphiql", Absinthe.Plug.GraphiQL,
      schema: DndAppWeb.GraphQL.Schema,
      interface: :playground
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
