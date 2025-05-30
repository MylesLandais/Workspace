# config/runtime.exs
import Config
import Dotenvy

source!(Path.expand(".env"))

config :nostrum,
  token: env!("DISCORD_TOKEN", :string!),
  gateway_intents: [:guilds, :guild_messages, :guild_voice_states, :message_content],
  youtubedl: "yt-dlp",
  ffmpeg: "ffmpeg"
  

config :nebulixir,
  discord_guild_id: env!("GUILD_ID", :string!)
