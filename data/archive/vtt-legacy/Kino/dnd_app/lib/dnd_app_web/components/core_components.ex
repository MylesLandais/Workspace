defmodule DndAppWeb.CoreComponents do
  @moduledoc """
  Provides core UI components.

  The components in this module use Tailwind CSS, a utility-first CSS framework.
  See the [Tailwind CSS documentation](https://tailwindcss.com) to learn how to
  customize the generated components in this module.
  """
  use Phoenix.Component

  @doc """
  Renders a page title.

  ## Examples

      <.live_title suffix=" · D&D App">
        <%= assigns[:page_title] || "D&D 5e Character Creator" %>
      </.live_title>
  """
  attr :suffix, :string, default: ""
  slot :inner_block, required: true

  def live_title(assigns) do
    ~H"""
    <title><%= render_slot(@inner_block) %><%= @suffix %></title>
    """
  end
end




