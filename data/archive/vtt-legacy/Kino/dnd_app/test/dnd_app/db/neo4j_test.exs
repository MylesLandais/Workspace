defmodule DndApp.DB.Neo4jTest do
  use ExUnit.Case, async: false
  alias DndApp.DB.Neo4j
  alias DndApp.Characters

  @moduletag :integration

  setup do
    # Clean up any test characters before each test
    on_exit(fn ->
      # This would clean up test data
      :ok
    end)

    :ok
  end

  describe "setup_schema/0" do
    test "creates constraints idempotently" do
      assert :ok = Neo4j.setup_schema()
      # Should be safe to call multiple times
      assert :ok = Neo4j.setup_schema()
    end
  end

  describe "upsert_character/1" do
    test "creates a new character" do
      character_data = %{
        id: UUID.uuid4(),
        name: "Test Character",
        level: 1,
        str: 15,
        dex: 14,
        con: 13,
        int: 12,
        wis: 10,
        cha: 8,
        str_mod: 2,
        dex_mod: 2,
        con_mod: 1,
        int_mod: 1,
        wis_mod: 0,
        cha_mod: -1,
        proficiency_bonus: 2,
        ac: 12,
        max_hp: 11,
        current_hp: 11,
        race: "Human",
        class: "Fighter",
        background: "Folk Hero",
        skills: []
      }

      assert {:ok, _} = Neo4j.upsert_character(character_data)
    end

    test "updates existing character" do
      character_data = %{
        id: UUID.uuid4(),
        name: "Update Test",
        level: 1,
        str: 10,
        dex: 10,
        con: 10,
        int: 10,
        wis: 10,
        cha: 10,
        str_mod: 0,
        dex_mod: 0,
        con_mod: 0,
        int_mod: 0,
        wis_mod: 0,
        cha_mod: 0,
        proficiency_bonus: 2,
        ac: 10,
        max_hp: 10,
        current_hp: 10,
        race: "Human",
        class: "Fighter",
        background: "Folk Hero",
        skills: []
      }

      {:ok, _} = Neo4j.upsert_character(character_data)

      # Update the character
      updated = Map.put(character_data, :name, "Updated Name")
      assert {:ok, _} = Neo4j.upsert_character(updated)
    end

    test "creates relationships to race, class, and background" do
      character_data = %{
        id: UUID.uuid4(),
        name: "Relationship Test",
        level: 1,
        str: 10,
        dex: 10,
        con: 10,
        int: 10,
        wis: 10,
        cha: 10,
        str_mod: 0,
        dex_mod: 0,
        con_mod: 0,
        int_mod: 0,
        wis_mod: 0,
        cha_mod: 0,
        proficiency_bonus: 2,
        ac: 10,
        max_hp: 10,
        current_hp: 10,
        race: "Elf",
        class: "Ranger",
        background: "Outlander",
        skills: []
      }

      assert {:ok, _} = Neo4j.upsert_character(character_data)
    end
  end

  describe "get_character/1" do
    test "retrieves character by ID" do
      attrs = %{
        name: "Get Test",
        race: "Human",
        class: "Fighter",
        background: "Folk Hero",
        str: 15,
        dex: 14,
        con: 13,
        int: 12,
        wis: 10,
        cha: 8
      }

      {:ok, created} = Characters.create_character(attrs)

      assert {:ok, retrieved} = Neo4j.get_character(created.id)
      assert retrieved.name == "Get Test"
      assert retrieved.race == "Human"
      assert retrieved.class == "Fighter"
      assert retrieved.str == 15
    end

    test "returns error for non-existent character" do
      fake_id = UUID.uuid4()
      assert {:error, :not_found} = Neo4j.get_character(fake_id)
    end
  end

  describe "list_characters/0" do
    test "returns list of characters" do
      # Create a test character
      attrs = %{
        name: "List Test",
        race: "Human",
        class: "Fighter",
        background: "Folk Hero",
        str: 10,
        dex: 10,
        con: 10,
        int: 10,
        wis: 10,
        cha: 10
      }

      {:ok, _} = Characters.create_character(attrs)

      assert {:ok, characters} = Neo4j.list_characters()
      assert is_list(characters)
      # Should contain at least our test character
      assert Enum.any?(characters, &(&1.name == "List Test"))
    end
  end

  describe "delete_character/1" do
    test "deletes character by ID" do
      attrs = %{
        name: "Delete Test",
        race: "Human",
        class: "Fighter",
        background: "Folk Hero",
        str: 10,
        dex: 10,
        con: 10,
        int: 10,
        wis: 10,
        cha: 10
      }

      {:ok, created} = Characters.create_character(attrs)

      assert :ok = Neo4j.delete_character(created.id)
      assert {:error, :not_found} = Neo4j.get_character(created.id)
    end
  end
end




