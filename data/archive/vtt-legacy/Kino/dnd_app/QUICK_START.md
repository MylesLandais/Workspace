# Quick Start - Get the Server Running

## The Problem
You're seeing "Unable to connect" because the Phoenix server isn't running yet.

## Solution: Start the Server

### Option 1: Use the Start Script (Easiest)

```bash
cd dnd_app
./start.sh
```

This script will:
- Check if Elixir is installed
- Install dependencies if needed
- Check Neo4j connection
- Start the server

### Option 2: Manual Start

**Step 1: Install Dependencies**
```bash
cd dnd_app
mix deps.get
cd assets && npm install && cd ..
```

**Step 2: Start Neo4j (if not running)**
```bash
docker run -d \
  --name neo4j-dnd \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community
```

**Step 3: Start the Server**
```bash
mix phx.server
```

**Step 4: Open Browser**
Navigate to: **http://localhost:4000**

## What You Should See

When the server starts successfully, you'll see:
```
[info] Running DndAppWeb.Endpoint with cowboy 2.x at http://127.0.0.1:4000 (http)
[info] Access DndAppWeb.Endpoint at http://localhost:4000
```

## Common Issues

### "mix: command not found"
**Problem:** Elixir is not installed.

**Solution:** Install Elixir:
- **macOS:** `brew install elixir`
- **Linux:** Use `asdf` or your package manager
- **Windows:** Download from elixir-lang.org

### "Neo4j connection failed"
**Problem:** Neo4j is not running.

**Solution:** Start Neo4j (see Step 2 above)

### "Port 4000 already in use"
**Problem:** Another application is using port 4000.

**Solution:** 
1. Find what's using it: `lsof -i :4000`
2. Stop that application, OR
3. Change port in `config/dev.exs` to 4001

### "Dependencies not found"
**Problem:** Dependencies aren't installed.

**Solution:** Run `mix deps.get`

## Still Can't Connect?

1. **Check the terminal** - Is the server actually running?
2. **Check for errors** - Look for red error messages
3. **Check Neo4j** - Is it running? `docker ps | grep neo4j`
4. **Try a different browser** - Sometimes browser cache causes issues
5. **Try http://127.0.0.1:4000** instead of localhost

## Need More Help?

See `TROUBLESHOOTING.md` for detailed troubleshooting steps.





