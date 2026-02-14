defmodule DndAppWeb.HomeLiveTest do
  use DndAppWeb.LiveCase

  describe "Home page" do
    test "renders dice roller", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/")

      assert has_element?(view, "h1", "D&D 5e Dice Roller")
      assert has_element?(view, "form")
      assert has_element?(view, "input[name='expression']")
      assert has_element?(view, "button", "Roll")
    end

    test "rolls dice with valid expression", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/")

      view
      |> form("form", %{expression: "1d20"})
      |> render_submit()

      assert has_element?(view, ".dice-result")
      assert has_element?(view, ".total")
    end

    test "shows error for invalid expression", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/")

      view
      |> form("form", %{expression: "invalid"})
      |> render_submit()

      assert has_element?(view, ".alert-error")
    end

    test "quick roll buttons work", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/")

      assert has_element?(view, "button[phx-click='quick_roll']", "d20")
      assert has_element?(view, "button[phx-click='quick_roll']", "d12")
      assert has_element?(view, "button[phx-click='quick_roll']", "4d6 (ability)")

      view
      |> element("button[phx-click='quick_roll'][phx-value-expression='1d20']")
      |> render_click()

      assert has_element?(view, ".dice-result")
    end

    test "displays dice result details", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/")

      view
      |> form("form", %{expression: "4d6dl1"})
      |> render_submit()

      assert has_element?(view, ".dice-result")
      assert has_element?(view, ".result-details")
      # Should show rolls
      assert render(view) =~ "Rolls:"
    end

    test "navigation links are present", %{conn: conn} do
      {:ok, _view, html} = live(conn, "/")

      assert html =~ ~r/href="\/characters\/new"/
      assert html =~ ~r/href="\/characters"/
    end
  end
end




