defmodule DndAppWeb.ErrorHTML do
  use DndAppWeb, :html

  # If you want to customize your error pages,
  # uncomment the embed_templates line and add the templates
  # to your error html files, e.g:
  #
  #   embed_templates "error_html/*"

  # The default is to render a plain text page based on
  # the template name. For example, "404.html" becomes
  # "Not Found".
  def render(template, _assigns) do
    Phoenix.Controller.status_message_from_template(template)
  end
end




