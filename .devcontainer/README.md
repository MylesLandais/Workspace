# DevContainer Setup

This directory contains the VS Code Dev Container configuration for the D&D Character Creator application.

## Prerequisites

1. **VS Code** with the **Dev Containers** extension installed, OR **Cursor** with Dev Containers support
2. **Docker** and **Docker Compose** installed and running

## Quick Start

### Option 1: Using VS Code / Cursor Dev Containers

1. **Install the Dev Containers extension** (if not already installed):
   - VS Code: Search for "Dev Containers" by Microsoft in Extensions
   - Cursor: May need to install "Dev Containers" extension manually

2. Open the project in VS Code/Cursor

3. **Reopen in Container**:
   - Press `F1` (or `Ctrl+Shift+P`) 
   - Type and select: **"Dev Containers: Reopen in Container"**
   - If that command doesn't exist, try: **"Remote-Containers: Reopen in Container"**

4. Wait for the container to build and start (first time may take a few minutes)

5. Once inside the container, run:
   ```bash
   cd dnd_app
   mix deps.get
   mix phx.server
   ```

6. Access the application at **http://localhost:4000**
7. Access Neo4j Browser at **http://localhost:7474** (username: `neo4j`, password: `password`)

### Option 2: Using Docker Compose Directly (If Dev Containers Extension Not Available)

If the Dev Containers extension isn't working in Cursor, you can use Docker Compose directly:

1. **Start the services**:
   ```bash
   cd .devcontainer
   docker-compose up -d
   ```

2. **Enter the app container**:
   ```bash
   docker-compose exec app bash
   ```

3. **Inside the container**:
   ```bash
   cd dnd_app
   mix deps.get
   mix phx.server
   ```

4. Access the application at **http://localhost:4000**
5. Access Neo4j Browser at **http://localhost:7474**

6. **To stop**:
   ```bash
   docker-compose down
   ```

## Services

### App Container
- **Elixir 1.17** with **Erlang/OTP 27**
- **Phoenix 1.7**
- **Node.js 20** for asset compilation
- Workspace mounted at `/workspace`
- ElixirLS LSP support for autocomplete and debugging

### Neo4j Service
- **Neo4j Latest** (5.x+)
- **Bolt Protocol**: Port 7687
- **Browser UI**: Port 7474
- **Container Name**: `neo4j-devcontainer` (to avoid conflicts with existing containers)
- **Credentials**: `neo4j` / `password`

## Port Conflicts

If you have existing containers using ports 4000, 7474, or 7687:

1. Stop existing containers:
   ```bash
   docker stop neo4j-dnd  # or your existing container name
   docker stop dnd-app    # if running
   ```

2. Or modify ports in `.devcontainer/docker-compose.yml` if needed

## Neo4j Initialization

Schema and sample data scripts are located in `.devcontainer/neo4j-init/`:

- `01-schema.cypher` - Creates database constraints
- `02-sample-data.cypher` - Creates sample characters for testing

### Loading Initialization Scripts

**Option 1: Via Neo4j Browser**
1. Open http://localhost:7474
2. Login with `neo4j` / `password`
3. Copy and paste the contents of the `.cypher` files into the query editor
4. Execute each script

**Option 2: Via cypher-shell**
```bash
docker exec neo4j-devcontainer cypher-shell -u neo4j -p password < .devcontainer/neo4j-init/01-schema.cypher
docker exec neo4j-devcontainer cypher-shell -u neo4j -p password < .devcontainer/neo4j-init/02-sample-data.cypher
```

## Configuration

### Neo4j Connection

The app automatically connects to Neo4j using the service name `neo4j` when running in the devcontainer. This is configured via environment variables in `docker-compose.yml`:

- `NEO4J_URL=bolt://neo4j:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=password`

For local development (outside devcontainer), the app defaults to `bolt://localhost:7687`.

### Environment Variables

You can override Neo4j settings by modifying `.devcontainer/docker-compose.yml` or setting environment variables in your shell.

## Development Workflow

1. **Start the devcontainer** (VS Code/Cursor handles this automatically, or use Docker Compose directly)
2. **Install dependencies** (runs automatically via `postCreateCommand` in devcontainer, or run `mix deps.get` manually)
3. **Start Phoenix server**: `mix phx.server` in the `dnd_app` directory
4. **Make code changes** - they're automatically synced via volume mount
5. **Hot reload** is enabled - changes to Elixir files trigger automatic recompilation

## Troubleshooting

### Dev Containers Command Not Found (Cursor)
- **Solution 1**: Install the "Dev Containers" extension manually in Cursor
- **Solution 2**: Use Docker Compose directly (see Option 2 above)
- **Solution 3**: Check if Cursor has built-in container support in settings

### Container won't start
- Check Docker is running: `docker ps`
- Check for port conflicts
- Rebuild container: `F1` → "Dev Containers: Rebuild Container" (or `docker-compose build`)

### Can't connect to Neo4j
- Verify Neo4j is healthy: `docker ps | grep neo4j-devcontainer`
- Check logs: `docker logs neo4j-devcontainer`
- Verify connection string in `dnd_app/config/config.exs`

### ElixirLS not working
- Ensure the extension is installed: `JakeBecker.elixir-ls`
- Restart VS Code/Cursor
- Check the Output panel for ElixirLS errors

### Assets not compiling
- Run `cd dnd_app/assets && npm install`
- Run `mix assets.deploy` or `mix phx.digest`

## Volumes

- `neo4j_data` - Persistent Neo4j database storage
- `neo4j_logs` - Neo4j log files
- Workspace - Your code (mounted from project root)

## Notes

- The devcontainer uses `sleep infinity` to keep the container running for development
- All mix commands work normally inside the container
- The Neo4j container name is `neo4j-devcontainer` to avoid conflicts with existing `neo4j-dnd` containers
- Data persists between container restarts via Docker volumes
- If Dev Containers extension doesn't work, you can always use Docker Compose directly
