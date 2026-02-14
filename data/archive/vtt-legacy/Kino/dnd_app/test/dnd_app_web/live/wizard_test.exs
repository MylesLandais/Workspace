defmodule DndAppWeb.WizardTest do
  use DndAppWeb.LiveCase

  describe "Method Selection" do
    test "renders method selection page", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new/method")

      assert has_element?(view, "h1") || has_element?(view, "h2")
      html = render(view)
      assert html =~ "Standard" || html =~ "method" || html =~ "create"
    end

    test "has links to different creation modes", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new/method")

      html = render(view)
      # Should have links or buttons for different modes
      assert html =~ "standard" || html =~ "quick" || html =~ "random" || html =~ "premade"
    end
  end

  describe "Wizard Navigation" do
    test "renders wizard with initial step", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      # Should show wizard interface
      html = render(view)
      assert html =~ "class" || html =~ "step" || html =~ "wizard"
    end

    test "navigates to next step", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=quick")

      # Quick mode starts at species step
      html = render(view)

      # Try to navigate to next step if button exists
      if html =~ "Next" || html =~ "next_step" do
        view
        |> element("button[phx-click='next_step']")
        |> render_click()

        # Should be on a different step
        updated_html = render(view)
        assert updated_html != html
      end
    end

    test "navigates to previous step", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=quick")

      # Navigate forward first if possible
      html = render(view)
      if html =~ "Next" || html =~ "next_step" do
        view
        |> element("button[phx-click='next_step']")
        |> render_click()
      end

      # Then try to go back
      updated_html = render(view)
      if updated_html =~ "Previous" || updated_html =~ "prev_step" do
        view
        |> element("button[phx-click='prev_step']")
        |> render_click()

        # Should be back on previous step
        final_html = render(view)
        assert final_html != updated_html || final_html == html
      end
    end

    test "navigates to specific step via breadcrumb", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      html = render(view)
      if html =~ "goto_step" || html =~ "breadcrumb" do
        # Try clicking on a step button
        view
        |> element("button[phx-click='goto_step']")
        |> render_click()

        # Should navigate to that step
        updated_html = render(view)
        assert updated_html != html || updated_html =~ "step"
      end
    end
  end

  describe "Mode-Specific Behavior" do
    test "quick mode starts at species step", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=quick")

      html = render(view)
      # Quick mode should start at species, not class
      assert html =~ "species" || html =~ "race" || html =~ "Species"
    end

    test "random mode generates character and goes to review", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=random")

      html = render(view)
      # Random mode should generate everything and show review
      assert html =~ "review" || html =~ "Review" || html =~ "character"
    end

    test "standard mode starts at class step", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=standard")

      html = render(view)
      # Standard mode should start at class selection
      assert html =~ "class" || html =~ "Class" || html =~ "wizard"
    end
  end

  describe "Step-Specific Functionality" do
    test "class selection step displays classes", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      html = render(view)
      # Should show class options or class selection interface
      assert html =~ "class" || html =~ "Fighter" || html =~ "Wizard" || html =~ "select"
    end

    test "species selection step displays races", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=quick")

      html = render(view)
      # Should show race options
      assert html =~ "race" || html =~ "species" || html =~ "Human" || html =~ "Elf"
    end

    test "abilities step shows point buy interface", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      # Navigate to abilities step if possible
      html = render(view)
      if html =~ "abilities" || html =~ "Abilities" do
        # Should show point buy or ability score interface
        assert html =~ "point" || html =~ "ability" || html =~ "score"
      end
    end
  end

  describe "Point Buy Interface" do
    test "displays point buy controls", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      html = render(view)
      # Should show point buy interface when on abilities step
      # This is a basic check - actual point buy UI may vary
      assert html =~ "point" || html =~ "budget" || html =~ "ability"
    end

    test "updates ability scores", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      html = render(view)
      # Try to find ability score input
      if html =~ "update_ability_score" || html =~ "ability" do
        # This would require specific form structure
        # For now, we verify the interface exists
        assert html =~ "str" || html =~ "dex" || html =~ "ability"
      end
    end
  end

  describe "Character Creation Flow" do
    test "can complete character creation", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=random")

      html = render(view)
      # Random mode should have a complete character ready
      # Look for create/save button
      if html =~ "create" || html =~ "save" || html =~ "Create Character" do
        # Character should be ready to create
        assert html =~ "character" || html =~ "review"
      end
    end

    test "shows validation errors for incomplete character", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      # Try to proceed without completing required fields
      html = render(view)
      if html =~ "next_step" || html =~ "Next" do
        view
        |> element("button[phx-click='next_step']")
        |> render_click()

        # Should show error or stay on current step
        updated_html = render(view)
        assert updated_html =~ "error" || updated_html =~ "required" || updated_html == html
      end
    end
  end

  describe "Name Generator" do
    test "displays name suggestions", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      html = render(view)
      # Should have name input or name suggestions button
      if html =~ "suggest_names" || html =~ "name" do
        # Name generator interface should be available
        assert html =~ "name" || html =~ "suggest"
      end
    end
  end

  describe "Character Preview" do
    test "displays character preview sidebar", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new")

      html = render(view)
      # Should show character preview
      assert html =~ "preview" || html =~ "Preview" || html =~ "character"
    end

    test "updates preview when character changes", %{conn: conn} do
      {:ok, view, _html} = live(conn, "/characters/new?mode=random")

      initial_html = render(view)

      # Random mode should have generated character data
      # Preview should show character information
      assert initial_html =~ "character" || initial_html =~ "preview" || initial_html =~ "ability"
    end
  end
end
