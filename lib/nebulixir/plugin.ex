defmodule Nebulixir.Plugin do
  @moduledoc """
  Behaviour for Nebulixir command plugins.

  Any module implementing this behaviour must provide:

    * `command_spec/0` – Returns a map defining the slash command (must include `:name` and `:description`).
    * `handle_command/2` – Handles the Discord interaction when the command is called.

  Use `use Nebulixir.Plugin` to set this behaviour in your plugin module.
  """

  @typedoc "Specification returned by a command plugin"
  @type command_spec :: %{
          required(:name) => String.t(),
          required(:description) => String.t(),
          optional(atom()) => any()
        }

  @typedoc "Interaction map from Discord"
  @type interaction :: map()

  @typedoc "API context passed by the PluginManager"
  @type api_context :: map()

  @callback command_spec() :: command_spec | {:error, String.t()}
  @callback handle_command(interaction(), api_context()) :: :ok | {:error, any()}

  @doc """
  Use this macro in your plugin modules to set the behaviour automatically.
  """
  defmacro __using__(_opts) do
    quote do
      @behaviour Nebulixir.Plugin
    end
  end
end
