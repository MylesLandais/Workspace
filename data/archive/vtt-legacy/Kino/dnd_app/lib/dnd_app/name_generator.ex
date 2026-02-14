defmodule DndApp.NameGenerator do
  @moduledoc """
  Name generator for character names.
  Supports API integration with fallback to local lists.
  """
  require Logger
  alias DndApp.NameGenerator.Fallback

  @api_url "https://api.fantasynamegenerator.com/api/v1"

  @doc """
  Suggest names for a character based on race and optional gender.
  Returns a list of name suggestions.
  """
  def suggest_names(race, opts \\ []) do
    gender = Keyword.get(opts, :gender, nil)
    count = Keyword.get(opts, :count, 5)

    case fetch_from_api(race, gender, count) do
      {:ok, names} ->
        names
      {:error, _reason} ->
        Logger.info("Name generator API unavailable, using fallback")
        Fallback.get_names(race, count)
    end
  end

  defp fetch_from_api(race, gender, count) do
    try do
      # Map D&D races to API-friendly names
      race_param = normalize_race_name(race)
      url = "#{@api_url}/names/#{race_param}"

      params = [
        count: count
      ]
      params = if gender, do: [{:gender, gender} | params], else: params

      case Req.get(url, params: params, receive_timeout: 5000) do
        {:ok, %{status: 200, body: body}} ->
          names = extract_names_from_response(body)
          if length(names) > 0 do
            {:ok, names}
          else
            {:error, :empty_response}
          end
        {:ok, %{status: status}} ->
          Logger.debug("Name generator API returned status #{status}")
          {:error, :api_error}
        {:error, %{reason: :timeout}} ->
          Logger.debug("Name generator API timeout")
          {:error, :timeout}
        {:error, reason} ->
          Logger.debug("Name generator API error: #{inspect(reason)}")
          {:error, reason}
      end
    rescue
      e ->
        Logger.debug("Name generator API exception: #{inspect(e)}")
        {:error, :exception}
    end
  end

  defp normalize_race_name(race) do
    race
    |> String.downcase()
    |> String.replace(" ", "-")
    |> String.replace("half-", "half")
  end

  defp extract_names_from_response(body) when is_list(body), do: body
  defp extract_names_from_response(%{"names" => names}) when is_list(names), do: names
  defp extract_names_from_response(%{"data" => names}) when is_list(names), do: names
  defp extract_names_from_response(_), do: []

  @doc """
  Get a random name for a race.
  """
  def random_name(race) do
    Fallback.get_names(race, 1) |> List.first() || "Unknown"
  end
end
