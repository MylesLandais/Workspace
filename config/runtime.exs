# config/runtime.exs
import Config
import Dotenvy

if File.exists?(".env") do
  source!(Path.expand(".env"))
end

config :nostrum,
  token: env!("DISCORD_TOKEN", :string!),
  gateway_intents: [:guilds, :guild_messages, :guild_voice_states, :message_content],
  youtubedl: "yt-dlp",
  ffmpeg: "ffmpeg",
  voice_log_level: :debug

config :nebulixir,
  discord_guild_id: env!("GUILD_ID", :string!)

