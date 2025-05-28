defmodule NebulixirTest do
  use ExUnit.Case
  doctest Nebulixir

  test "greets the world" do
    assert Nebulixir.hello() == :world
  end
end
