# Nebulixir

**Elixir Discord Bot that uses a HOT LOADING plugin system**

## Installation
Windows Installation:

Ensure that you have Erlang installed - Erlang/OTP 27 [erts-15.2.2]

Ensure that you have Elixir installed - Elixir 1.18.4 (compiled with Erlang/OTP 27)

Clone this REPO

Go to project directory & type mix deps.get to install the depenencies
&& mix compile

to run the project please create a .env file in the main directory with your discord token & guild ID

example .env file:
```
DISCORD_TOKEN=YOUR TOKEN GOES HERE
GUILD_ID=GUILDID GOES HERE
```

Use mix run --no-halt to run the project!


## Features:
Hot loading plugin system - drag & drop plugins into the lib/plugins folder to install them as a slash command!
Need to fix a plugin but can't afford the downtime? No problem! Just edit your plugin and it will automatically update your slash command and your edits will be made!

Examples available in /lib/nebulixir/plugins
