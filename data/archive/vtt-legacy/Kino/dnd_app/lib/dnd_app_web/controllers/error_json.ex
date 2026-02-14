defmodule DndAppWeb.ErrorJSON do
  # If you want to customize your error pages,
  # uncomment the embed_templates line and add the templates
  # to your error json files, e.g:
  #
  #   embed_templates "error_json/*"

  def render(template, _assigns) do
    %{errors: %{detail: Phoenix.Controller.status_message_from_template(template)}}
  end
end




