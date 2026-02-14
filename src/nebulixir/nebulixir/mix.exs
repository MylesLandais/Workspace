defmodule Nebulixir.MixProject do
  use Mix.Project

  def project do

    [
      app: :nebulixir,
      version: "0.1.0",
      elixir: "~> 1.18",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [
      extra_applications: [:logger, :nostrum, :file_system, :jason, :dotenvy], # Keep other necessary apps
      mod: {Nebulixir.Application, []}
    ]
  end

  defp deps do
    [
      {:nostrum, "~> 0.10"},
      {:file_system, "~> 1.0"},
      {:jason, "~> 1.4"},
      {:dotenvy, "~> 1.0.0"}
    ]
  end
end
