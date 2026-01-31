{
  pkgs,
  lib,
  config,
  ...
}:
{
  packages = [
    pkgs.lighthouse
    pkgs.otel-cli
    pkgs.vips
    pkgs.pkg-config
    pkgs.python3
    pkgs.mysql84        # MySQL client for db access
    pkgs.just           # Task runner
    pkgs.netcat-gnu     # For wait-for-db TCP checks
    pkgs.curl           # For health checks
  ];

  # Force Sharp to use system-installed vips (prevents downloading broken binaries)
  env.SHARP_IGNORE_GLOBAL_LIBVIPS = "0";

  env.LD_LIBRARY_PATH = lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.vips
  ];

  languages = {
    javascript = {
      enable = true;
      bun = {
        enable = true;
        install.enable = false;
      };
    };
  };

  # Shared services - managed by data engineering/MLOps team
  # Containers: cache.jupyter.dev.local, n4j.jupyter.dev.local, s3.jupyter.dev.local, mysql-scheduler.jupyter.dev.local
  env = {
    # MySQL (shared: mysql-scheduler.jupyter.dev.local on port 3307)
    MYSQL_HOST = "localhost";
    MYSQL_PORT = "3307";
    MYSQL_USER = "root";
    MYSQL_PASSWORD = "secret";
    MYSQL_DATABASE = "bunny_auth";

    # Valkey/Redis (shared: cache.jupyter.dev.local)
    REDIS_URL = "redis://localhost:6379";
    VALKEY_URL = "redis://localhost:6379";

    # Neo4j (shared: n4j.jupyter.dev.local)
    NEO4J_URI = "bolt://localhost:7687";
    NEO4J_USER = "neo4j";
    NEO4J_PASSWORD = "password";

    # MinIO (shared: s3.jupyter.dev.local)
    MINIO_ENDPOINT = "http://localhost:9000";
    MINIO_ACCESS_KEY = "minioadmin";
    MINIO_SECRET_KEY = "minioadmin";
    MINIO_BUCKET = "uploads";

    # OpenTelemetry (optional)
    OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318";
    OTEL_SERVICE_NAME = "bunny";
  };

  process.manager.implementation = "process-compose";

  process.managers.process-compose = {
    tui.enable = false;
  };

  # Application processes only - backing services are shared
  processes = {
    web = {
      exec = "cd app/client && bun run dev";
      process-compose = {
        depends_on.wait-for-db.condition = "process_completed_successfully";
      };
    };
    collab.exec = "cd app/client && node server/yjs-server.cjs";

    # Wait for shared MySQL to be ready (simple TCP check)
    wait-for-db = {
      exec = ''
        echo "Waiting for shared MySQL (port 3307)..."
        while ! nc -z localhost 3307 2>/dev/null; do
          echo "MySQL not ready, waiting..."
          sleep 2
        done
        sleep 1
        echo "MySQL is ready!"
      '';
      process-compose = {
        is_tty = false;
      };
    };
  };

  scripts = {
    # Check shared services status
    services-status.exec = ''
      echo "Shared Services Status:"
      echo ""
      echo "MySQL (mysql-scheduler.jupyter.dev.local:3307):"
      docker ps --filter name=mysql-scheduler.jupyter.dev.local --format "  {{.Status}}" || echo "  Not running"
      echo ""
      echo "Valkey (cache.jupyter.dev.local:6379):"
      docker ps --filter name=cache.jupyter.dev.local --format "  {{.Status}}" || echo "  Not running"
      echo ""
      echo "Neo4j (n4j.jupyter.dev.local:7474/7687):"
      docker ps --filter name=n4j.jupyter.dev.local --format "  {{.Status}}" || echo "  Not running"
      echo ""
      echo "MinIO (s3.jupyter.dev.local:9000):"
      docker ps --filter name=s3.jupyter.dev.local --format "  {{.Status}}" || echo "  Not running"
    '';

    # Wait utilities (simple TCP checks for reliability)
    wait-for-db.exec = ''
      echo "Waiting for shared MySQL (port 3307)..."
      while ! nc -z localhost 3307 2>/dev/null; do
        sleep 2
      done
      echo "MySQL ready!"
    '';

    wait-for-all.exec = ''
      echo "Checking shared services..."

      echo "Checking MySQL (port 3307)..."
      while ! nc -z localhost 3307 2>/dev/null; do sleep 2; done
      echo "MySQL ready!"

      echo "Checking Valkey (port 6379)..."
      while ! nc -z localhost 6379 2>/dev/null; do sleep 2; done
      echo "Valkey ready!"

      echo "Checking Neo4j (port 7474)..."
      while ! nc -z localhost 7474 2>/dev/null; do sleep 2; done
      echo "Neo4j ready!"

      echo "All shared services ready!"
    '';

    # Database operations
    db-push.exec = "cd app/client && bun run db:push";
    db-studio.exec = "cd app/client && bun run db:studio";
    db-shell.exec = "mysql -h localhost -P 3307 -u root -psecret bunny_auth";
    db-create.exec = ''
      docker exec mysql-scheduler.jupyter.dev.local mysql -u root -psecret -e "CREATE DATABASE IF NOT EXISTS bunny_auth;"
      echo "Database bunny_auth created/verified"
    '';

    # Build and test
    build-stack.exec = "cd app/client && bun run build";
    test-stack.exec = "cd app/client && bun test";
    e2e.exec = "cd app/client && bun run test:e2e";
    analyze-perf.exec = "lighthouse http://localhost:3000 --view";

    # GraphQL server
    server-start.exec = "cd app/server && docker compose up -d";
    server-stop.exec = "cd app/server && docker compose down";
    server-logs.exec = "cd app/server && docker compose logs -f";
    server-status.exec = "cd app/server && docker compose ps";
  };

  git-hooks.hooks = {
    nil.enable = true;
    prettier.enable = true;
    eslint.enable = true;
  };

  dotenv.disableHint = true;

  claude.code = {
    enable = true;

    agents = {
      frontend-specialist = {
        description = "Next.js 15, shadcn/ui, and Bun runtime expert";
        proactive = true;
        tools = [ "Read" "Write" "Edit" "Grep" "Bash" ];
        prompt = ''
          You are a Next.js 15 and shadcn/ui specialist using Bun runtime.

          Core principles:
          - Use App Router (not Pages Router)
          - Server components by default, client components only when needed
          - TypeScript strict mode always
          - Use shadcn/ui components via MCP server (never guess props)
          - Prefer Bun native APIs over Node.js alternatives (Bun.file, Bun.serve)
          - Tailwind CSS for all styling
          - Responsive design (mobile-first)

          File structure:
          - Components: app/client/src/components/[feature]/[Component].tsx
          - Hooks: app/client/src/hooks/[hookName].ts
          - Utils: app/client/src/lib/utils/[utility].ts
          - API routes: app/client/app/api/[endpoint]/route.ts

          Always verify component props via shadcn MCP before implementation.
        '';
      };

      backend-specialist = {
        description = "Elysia.js API development with Bun runtime";
        proactive = true;
        tools = [ "Read" "Write" "Edit" "Grep" "Bash" ];
        prompt = ''
          You specialize in Elysia.js backend development on Bun runtime.

          Best practices:
          - Type-safe routing with Elysia schemas (t.Object, t.String, t.Number)
          - Proper error handling and validation
          - RESTful API design principles
          - Use Bun native APIs when possible (Bun.file for uploads, Bun.write)
          - Implement CORS, rate limiting via Elysia plugins
          - Lifecycle hooks (beforeHandle, afterHandle) for auth/logging
          - GraphQL integration where appropriate

          File structure:
          - Routes: app/server/src/routes/[resource].ts
          - Services: app/server/src/services/[service].ts
          - Neo4j queries: app/server/src/neo4j/queries/[domain].ts
          - Bunny resolvers: app/server/src/bunny/resolvers.ts

          Always use connection pooling for databases.
        '';
      };

      database-architect = {
        description = "Multi-database strategy and optimization specialist";
        proactive = false;
        tools = [ "Read" "Write" "Grep" "Bash" ];
        prompt = ''
          You architect database solutions across the Bunny stack.

          Shared services (managed by data engineering/MLOps):
          - MySQL: mysql-scheduler.jupyter.dev.local (port 3307)
          - Valkey: cache.jupyter.dev.local (port 6379)
          - Neo4j: n4j.jupyter.dev.local (ports 7474/7687)
          - MinIO: s3.jupyter.dev.local (ports 9000/9001)

          Database roles:
          - MySQL: Relational data, user auth, sessions (Better Auth)
          - Valkey: Caching, session storage, pub/sub, rate limiting
          - Neo4j: Graph relationships, feed algorithms, social connections
          - MinIO: Object storage (images, avatars, media files)

          Guidelines:
          - MySQL: Use transactions for mutations, connection pooling, parameterized queries
          - Valkey: Set appropriate TTLs, use key prefixes (user:123:session), leverage pub/sub
          - Neo4j: Write efficient Cypher queries, use indexes, avoid Cartesian products
          - MinIO: Organize by bucket per environment, use presigned URLs for uploads
        '';
      };

      devops-engineer = {
        description = "Service management, containers, and deployment specialist";
        proactive = false;
        tools = [ "Read" "Write" "Bash" ];
        prompt = ''
          You handle infrastructure and deployment for the Bunny project.

          Shared services model:
          - Backing services are managed by data engineering/MLOps team
          - Bunny connects to shared MySQL, Valkey, Neo4j, MinIO
          - Only application containers are project-specific

          Commands:
          - services-status: Check shared service health
          - wait-for-all: Wait for all shared services
          - db-create: Create bunny_auth database if missing
          - server-start/stop: Manage GraphQL server container
        '';
      };
    };

    commands = {
      dev-all = ''
        Start development (requires shared services to be running)
        ```bash
        wait-for-all && devenv up
        ```
      '';

      test-suite = ''
        Run complete test suite (unit + E2E)
        ```bash
        cd app/client && bun test && bun run e2e
        ```
      '';

      db-migrate = ''
        Run database migrations (Drizzle)
        ```bash
        cd app/client && bun run db:push
        ```
      '';

      db-studio = ''
        Open Drizzle Studio for database inspection
        ```bash
        cd app/client && bun run db:studio
        ```
      '';

      build-prod = ''
        Build production containers for client and server
        ```bash
        devenv container build processes
        ```
      '';

      server-logs = ''
        View GraphQL server logs
        ```bash
        cd app/server && docker compose logs -f server
        ```
      '';
    };

    mcpServers = {
      shadcn = {
        type = "stdio";
        command = "npx";
        args = [ "shadcn@latest" "mcp" ];
      };
    };

    hooks = {
      protect-secrets = {
        enable = true;
        name = "Prevent editing sensitive files";
        hookType = "PreToolUse";
        matcher = "^(Edit|MultiEdit|Write)$";
        command = ''
          json=$(cat)
          file_path=$(echo "$json" | ${pkgs.jq}/bin/jq -r '.file_path // empty')

          if [[ "$file_path" =~ \.(env|secret|key)$ ]] || [[ "$file_path" =~ /\.env ]]; then
            echo "Error: Cannot edit sensitive files (.env, .secret, .key)"
            exit 1
          fi
        '';
      };

      test-on-typescript-save = {
        enable = true;
        name = "Run tests after TypeScript edits";
        hookType = "PostToolUse";
        matcher = "^(Edit|MultiEdit|Write)$";
        command = ''
          json=$(cat)
          file_path=$(echo "$json" | ${pkgs.jq}/bin/jq -r '.file_path // empty')

          if [[ "$file_path" =~ \.tsx?$ ]] && [[ "$file_path" =~ app/client/ ]]; then
            echo "Running tests for modified TypeScript file..."
            cd app/client && bun test --filter="**/*.test.ts" --bail
          fi
        '';
      };
    };
  };

  enterShell = ''
    echo "Bunny dev environment ready"
    echo ""
    echo "Shared Services (managed by data engineering/MLOps):"
    echo "  MySQL     - localhost:3307 (mysql-scheduler.jupyter.dev.local)"
    echo "  Valkey    - localhost:6379 (cache.jupyter.dev.local)"
    echo "  Neo4j     - localhost:7474/7687 (n4j.jupyter.dev.local)"
    echo "  MinIO     - localhost:9000 (s3.jupyter.dev.local)"
    echo ""
    echo "Commands:"
    echo "  services-status  - Check shared service health"
    echo "  wait-for-all     - Wait for all services to be ready"
    echo "  devenv up        - Start Next.js and Yjs"
    echo "  db-push          - Push MySQL schema"
    echo "  db-studio        - Open Drizzle Studio"
    echo "  db-shell         - MySQL CLI"
    echo ""
    echo "Quick start: wait-for-all && devenv up"
    echo ""
    if [ ! -d "app/client/node_modules" ]; then
      echo "Installing client dependencies..."
      (cd app/client && bun install)
    fi
  '';

}
