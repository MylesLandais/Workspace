# Nebulixir

**Elixir Discord Bot that uses a HOT LOADING plugin system**

## Installation
Windows Intallation:

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

