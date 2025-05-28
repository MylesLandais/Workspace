# config/runtime.exs
import Config
import Dotenvy

# Load .env file
source!(Path.expand(".env"))

# Debug prints (just for now)
#IO.inspect(System.get_env("GUILD_ID"), label: "System GUILD_ID")
#IO.inspect(env!("GUILD_ID", :string!), label: "Dotenvy GUILD_ID")

# Apply config
config :nostrum,
  token: env!("DISCORD_TOKEN", :string!),
  gateway_intents: [:guilds, :guild_messages]

config :nebulixir,
  discord_guild_id: env!("GUILD_ID", :string!)
