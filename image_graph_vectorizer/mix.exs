defmodule ImageGraphVectorizer.MixProject do
  use Mix.Project

  def project do
    [
      app: :image_graph_vectorizer,
      version: "0.1.0",
      elixir: "~> 1.14",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [
      extra_applications: [:logger, :crypto],
      mod: {ImageGraphVectorizer.Application, []}
    ]
  end

  defp deps do
    [
      # Neo4j Driver
      {:bolt_sips, "~> 2.0"},
      
      # File System Watcher
      {:file_system, "~> 1.0"},
      
      # HTTP Client for Embedding API
      {:req, "~> 0.4.0"},
      
      # JSON Handling
      {:jason, "~> 1.4"},
      
      # UUID Generation
      {:uuid, "~> 1.1"},
      
      # Testing
      {:ex_unit, "~> 1.14", only: :test}
    ]
  end
end