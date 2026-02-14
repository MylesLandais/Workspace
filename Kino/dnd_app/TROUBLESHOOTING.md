# Troubleshooting Guide

## Server Won't Start / Can't Connect to localhost:4000

### Step 1: Check if Server is Running

```bash
# Check if port 4000 is in use
lsof -i :4000
# or
netstat -tuln | grep :4000
```

If nothing shows up, the server is not running.

### Step 2: Verify Dependencies

```bash
cd dnd_app

# Check if dependencies are installed
ls deps/ 2>/dev/null && echo "Dependencies exist" || echo "Need to install dependencies"

# Install if needed
mix deps.get
```

### Step 3: Check for Compilation Errors

```bash
# Try to compile
mix compile

# Look for errors in the output
```

Common issues:
- Missing dependencies → Run `mix deps.get`
- Compilation errors → Fix code issues
- Missing Erlang/Elixir → Install Elixir 1.14+

### Step 4: Check Neo4j Connection

The server requires Neo4j to start. Check if Neo4j is running:

```bash
# Check if Neo4j is running (Docker)
docker ps | grep neo4j

# Or check if port 7687 is open
lsof -i :7687
```

If Neo4j is not running, start it:

```bash
docker run -d \
  --name neo4j-dnd \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community
```

### Step 5: Start the Server

```bash
# Make sure you're in the dnd_app directory
cd dnd_app

# Start the server
mix phx.server
```

**Expected output:**
```
[info] Running DndAppWeb.Endpoint with cowboy 2.x at http://127.0.0.1:4000 (http)
[info] Access DndAppWeb.Endpoint at http://localhost:4000
```

### Step 6: Check for Errors

If the server fails to start, look for error messages:

**Common Errors:**

1. **"Could not find application"**
   ```bash
   mix deps.get
   mix deps.compile
   ```

2. **"Neo4j connection failed"**
   - Check Neo4j is running
   - Verify credentials in `config/config.exs`
   - Check connection: `cypher-shell -u neo4j -p password`

3. **"Port already in use"**
   - Change port in `config/dev.exs`:
     ```elixir
     http: [ip: {127, 0, 0, 1}, port: 4001]
     ```

4. **"Module not found"**
   - Run `mix compile` to see specific errors
   - Check all files are in place

5. **"Assets not found"**
   ```bash
   cd assets && npm install && cd ..
   mix assets.deploy
   ```

### Step 7: Verify Installation

Check if Elixir is installed:

```bash
elixir --version
mix --version
```

If not installed, install Elixir:
- **macOS:** `brew install elixir`
- **Linux:** Use your package manager or `asdf`
- **Windows:** Download installer from elixir-lang.org

### Step 8: Clean Build (If All Else Fails)

```bash
cd dnd_app

# Clean everything
rm -rf _build deps

# Reinstall
mix deps.get
mix deps.compile
mix compile

# Install assets
cd assets && npm install && cd ..

# Try starting again
mix phx.server
```

### Step 9: Check Logs

When starting the server, watch for:
- ✅ "Neo4j schema initialized successfully"
- ✅ "Running DndAppWeb.Endpoint at http://127.0.0.1:4000"
- ❌ Any error messages (connection errors, compilation errors, etc.)

### Step 10: Alternative - Use IEx

If the server won't start, try interactive mode:

```bash
iex -S mix phx.server
```

This will give you an interactive console where you can see errors more clearly.

## Quick Diagnostic Commands

Run these to diagnose:

```bash
cd dnd_app

# 1. Check Elixir
elixir --version

# 2. Check dependencies
mix deps

# 3. Check compilation
mix compile

# 4. Check Neo4j
docker ps | grep neo4j || echo "Neo4j not running"

# 5. Check port
lsof -i :4000 || echo "Port 4000 free"

# 6. Try to start
mix phx.server
```

## Still Having Issues?

1. **Check the error message** - It usually tells you what's wrong
2. **Check Neo4j** - The app requires Neo4j to start
3. **Check dependencies** - All deps must be installed
4. **Check compilation** - Code must compile without errors
5. **Check logs** - Server logs show what's happening

## Getting Help

When asking for help, provide:
1. Error message (full text)
2. Output of `mix phx.server`
3. Output of `mix deps`
4. Whether Neo4j is running
5. Elixir version: `elixir --version`





