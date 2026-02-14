# Start Server with Existing Neo4j Container

## Current Setup

✅ **Neo4j is already running** in a container on:
- Port 7474 (HTTP)
- Port 7687 (Bolt protocol)

## Quick Start

Since Neo4j is already running, you just need to start the Phoenix app:

### Option 1: Run Locally (Easiest)

```bash
cd dnd_app

# 1. Install dependencies (if not done)
mix deps.get
cd assets && npm install && cd ..

# 2. Start the Phoenix server
mix phx.server
```

The app will connect to Neo4j at `localhost:7687` (which is your container).

### Option 2: Use Docker Compose

If you want everything in containers:

```bash
cd dnd_app

# Comment out or remove the neo4j service in docker-compose.yml
# Then start just the app:
docker-compose up dnd-app
```

## Verify Neo4j Connection

Test that Neo4j is accessible:

```bash
# Check container is running
docker ps | grep neo4j

# Test connection (if you have cypher-shell)
cypher-shell -u neo4j -p password "RETURN 1"
```

## Configuration

The app is already configured to connect to `localhost:7687` in `config/config.exs`:

```elixir
config :bolt_sips, Bolt,
  url: "bolt://localhost:7687",
  basic_auth: [username: "neo4j", password: "password"],
```

**If your Neo4j container uses different credentials**, update the config file.

## Start the Server

```bash
cd dnd_app
mix phx.server
```

You should see:
```
[info] Running DndAppWeb.Endpoint with cowboy 2.x at http://127.0.0.1:4000 (http)
[info] Access DndAppWeb.Endpoint at http://localhost:4000
```

Then open: **http://localhost:4000**

## Troubleshooting

### "Neo4j connection failed"

1. Check Neo4j container is running:
   ```bash
   docker ps | grep neo4j
   ```

2. Check Neo4j credentials match your container:
   - Default in config: `neo4j/password`
   - If different, update `config/config.exs`

3. Test connection manually:
   ```bash
   docker exec neo4j cypher-shell -u neo4j -p password "RETURN 1"
   ```

### "Port 4000 already in use"

Change port in `config/dev.exs`:
```elixir
http: [ip: {127, 0, 0, 1}, port: 4001],
```

Then access: http://localhost:4001

### "mix: command not found"

Elixir is not installed on your host. Options:
1. Install Elixir locally
2. Use Docker Compose (see `CONTAINER_SETUP.md`)
3. Run in a container with Elixir

## Next Steps

Once the server starts:
1. Open http://localhost:4000
2. Test the dice roller
3. Create a character
4. See `UAT_GUIDE.md` for full testing checklist





