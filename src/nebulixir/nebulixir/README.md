# Nebulixir

Nebulixir is a modular, hot-reloadable Discord bot framework written in Elixir, built for speed, flexibility, and developer happiness.

---

## Features

* 🔥 **Hot-reloadable plugin system** — drag & drop plugins into `/lib/nebulixir/plugins` to register them as slash commands
* 🎵 **Voice playback** with YouTube and direct audio support
* 📝 **Clean, extensible command registration**
* 🛠️ **Built on [Nostrum](https://github.com/Kraigie/nostrum)** for Discord API integration

---

## Requirements

* **Erlang/OTP 27** (\[erts-15.2.2] recommended)
* **Elixir 1.18.4** (compiled with Erlang/OTP 27)
* **FFmpeg** (for audio transcoding)
* **yt-dlp** (YouTube audio extraction)
* \[Optional] **Streamlink** (for Twitch or other live streams)
* **Git**, **Python 3** (for yt-dlp)
* Supported on **Ubuntu 22.04+** and **Windows 10+**

---

## Installation

### Ubuntu (Recommended)

```sh
sudo apt update
sudo apt install -y git build-essential ffmpeg python3-pip

# Install Erlang/OTP 27 and Elixir 1.18.4 using asdf (recommended)
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
source ~/.bashrc

asdf plugin add erlang
asdf plugin add elixir

asdf install erlang 27.2.2
asdf install elixir 1.18.4

asdf global erlang 27.2.2
asdf global elixir 1.18.4

# Install yt-dlp
python3 -m pip install -U yt-dlp

# Clone Nebulixir and install dependencies
git clone https://github.com/YOUR-USERNAME/nebulixir.git
cd nebulixir
mix deps.get
mix compile
```

### Windows

1. **Install [Erlang/OTP 27](https://www.erlang.org/downloads) and [Elixir 1.18.4](https://elixir-lang.org/install.html)**
2. **Install [FFmpeg](https://ffmpeg.org/download.html) and ensure it's in your PATH**
3. **Install Python 3 and yt-dlp:**
   Open Command Prompt (as Administrator) and run:

   ```
   pip install -U yt-dlp
   ```
4. **Clone this repo:**

   ```
   git clone https://github.com/System-Nebula/nebulixir.git
   cd nebulixir
   mix deps.get
   mix compile
   ```

---

## Configuration

1. Create a `.env` file in the project root with your Discord credentials:

   ```
   DISCORD_TOKEN=your_token_here
   GUILD_ID=your_guild_id_here
   ```

2. **(Optional)** If you do not require Twitch/streamlink support, add this to `config/config.exs`:

   ```elixir
   config :nostrum, streamlink: nil
   ```

---

## Running Nebulixir

```sh
mix run --no-halt
```

The bot will start, load plugins from `lib/nebulixir/plugins`, and connect to Discord.
Slash commands will be registered automatically.

---

## Development

* Add plugins in `lib/nebulixir/plugins`
* Code changes are hot-reloaded on save (no restart needed!)
* Built-in commands: `/ping`, `/echo`, `/help`, `/play`
* Example plugins available in `lib/nebulixir/plugins`

---

## License

MIT

---

Happy hacking! 🚀
