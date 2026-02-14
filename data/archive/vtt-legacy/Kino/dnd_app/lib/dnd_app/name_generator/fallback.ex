defmodule DndApp.NameGenerator.Fallback do
  @moduledoc """
  Fallback name lists for when the API is unavailable.
  """

  @names_by_race %{
    "Human" => [
      "Aldric", "Brenna", "Cedric", "Dara", "Ewan", "Fiona", "Gareth", "Helena",
      "Ivan", "Jenna", "Kieran", "Lydia", "Marcus", "Nora", "Owen", "Petra",
      "Quinn", "Rhea", "Silas", "Tara", "Ulric", "Vera", "Wade", "Yara", "Zane"
    ],
    "Elf" => [
      "Aelar", "Arianna", "Celeborn", "Elara", "Faelan", "Galadriel", "Haldir",
      "Ithilien", "Liriel", "Mithrandir", "Nimue", "Olorin", "Rian", "Sindar",
      "Thranduil", "Varda", "Yavanna", "Zephyr"
    ],
    "Dwarf" => [
      "Balin", "Dwalin", "Fili", "Kili", "Gimli", "Thorin", "Bofur", "Bombur",
      "Dori", "Nori", "Ori", "Oin", "Gloin", "Bifur", "Durin", "Thrain",
      "Thror", "Dis"
    ],
    "Halfling" => [
      "Bilbo", "Frodo", "Samwise", "Pippin", "Merry", "Rosie", "Lobelia",
      "Hamfast", "Bell", "Primula", "Drogo", "Peregrin", "Meriadoc", "Paladin"
    ],
    "Dragonborn" => [
      "Arjhan", "Balasar", "Bharash", "Donaar", "Ghesh", "Heskan", "Kriv",
      "Medrash", "Mehen", "Nadarr", "Pandjed", "Patrin", "Rhogar", "Shamash",
      "Shedinn", "Tarhun", "Torinn"
    ],
    "Gnome" => [
      "Alston", "Alvyn", "Boddynock", "Brocc", "Burgell", "Dimble", "Eldon",
      "Erky", "Fonkin", "Frug", "Gerbo", "Gimble", "Glim", "Jebeddo", "Kellen",
      "Namfoodle", "Orryn", "Roondar", "Seebo", "Sindri", "Warryn", "Wrenn",
      "Zook"
    ],
    "Half-Elf" => [
      "Adran", "Aelar", "Aramil", "Arannis", "Aust", "Beiro", "Berrian",
      "Carric", "Enialis", "Erdan", "Erevan", "Galinndan", "Hadarai", "Heian",
      "Himo", "Immeral", "Ivellios", "Laucian", "Mindartis", "Paelias",
      "Peren", "Quarion", "Riardon", "Rolen", "Soveliss", "Thamior", "Tharivol",
      "Theren", "Varis"
    ],
    "Half-Orc" => [
      "Dench", "Feng", "Gell", "Henk", "Holg", "Imsh", "Keth", "Krusk",
      "Mhurren", "Ront", "Shump", "Thokk"
    ],
    "Tiefling" => [
      "Akmenos", "Amnon", "Barakas", "Damakos", "Ekemon", "Iados", "Kairon",
      "Leucis", "Melech", "Mordai", "Morthos", "Pelaios", "Skamos", "Therai"
    ]
  }

  @doc """
  Get a list of names for a given race.
  """
  def get_names(race_name, count \\ 5) do
    names = Map.get(@names_by_race, race_name, @names_by_race["Human"])
    names |> Enum.take_random(count)
  end

  @doc """
  Get all available names for a race.
  """
  def all_names(race_name) do
    Map.get(@names_by_race, race_name, @names_by_race["Human"])
  end
end
