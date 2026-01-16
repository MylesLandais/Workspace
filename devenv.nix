{
  pkgs,
  lib,
  config,
  ...
}:
let
  envOr = name: default:
    let value = builtins.getEnv name;
    in if value != "" then value else default;

  projectHash = builtins.hashString "sha256" (toString ./.);
  hashPrefix = lib.strings.substring 0 12 projectHash;
  hashSuffix = lib.strings.substring 12 24 projectHash;

  mysqlPassword = envOr "DEVENV_MYSQL_PASSWORD" "dev_${hashPrefix}_mysql";
  minioAccessKey = envOr "DEVENV_MINIO_ACCESS_KEY" "dev_${hashPrefix}_minio";
  minioSecretKey = envOr "DEVENV_MINIO_SECRET_KEY" "dev_${hashPrefix}_secret_${hashSuffix}";
in
{
  packages = [
    pkgs.lighthouse
    pkgs.otel-cli
    pkgs.vips
    pkgs.pkg-config
    pkgs.python3
  ];

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

  services = {
    mysql = {
      enable = true;
      initialDatabases = [ { name = "bunny_auth"; } ];
      ensureUsers = [
        {
          name = "user";
          password = mysqlPassword;
          ensurePermissions = {
            "bunny_auth.*" = "ALL PRIVILEGES";
          };
        }
      ];
    };
    redis = {
      enable = true;
      package = pkgs.valkey;
      port = 6379;
    };
    minio = {
      enable = true;
      buckets = [ "uploads" ];
    };
    opentelemetry-collector = {
      enable = true;
      settings = {
        receivers.otlp.protocols = {
          grpc.endpoint = "127.0.0.1:4317";
          http.endpoint = "127.0.0.1:4318";
        };
        exporters.debug = { };
        service.pipelines.traces = {
          receivers = [ "otlp" ];
          exporters = [ "debug" ];
        };
      };
    };
  };

  env = {
    MYSQL_HOST = "localhost";
    MYSQL_USER = "user";
    MYSQL_PASSWORD = mysqlPassword;
    MYSQL_DATABASE = "bunny_auth";

    REDIS_URL = "redis://localhost:6379";
    VALKEY_URL = "redis://localhost:6379";

    NEO4J_URI = "bolt://localhost:7687";
    NEO4J_USER = "neo4j";
    NEO4J_PASSWORD = "dev_password";

    MINIO_ENDPOINT = "http://localhost:9000";
    MINIO_ACCESS_KEY = minioAccessKey;
    MINIO_SECRET_KEY = minioSecretKey;
    MINIO_BUCKET = "uploads";

    OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318";
    OTEL_SERVICE_NAME = "bunny";
  };

  process.manager.implementation = "process-compose";

  process.managers.process-compose = {
    tui.enable = false;
  };

  processes = {
    web.exec = "cd app/client && bun run dev";
    collab.exec = "cd app/client && node server/yjs-server.cjs";
    neo4j = {
      exec = ''
        mkdir -p .devenv/state/neo4j/{data,logs,conf}
        ${pkgs.docker}/bin/docker run --rm \
          --name neo4j-devenv \
          -p 7474:7474 \
          -p 7687:7687 \
          -v $(pwd)/.devenv/state/neo4j/data:/data \
          -v $(pwd)/.devenv/state/neo4j/logs:/logs \
          -e NEO4J_AUTH=neo4j/dev_password \
          -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
          neo4j:5-community
      '';
    };
  };

  scripts = {
    build-stack.exec = "cd app/client && bun run build";
    test-stack.exec = "cd app/client && bun test";
    e2e.exec = "cd app/client && bun run test:e2e";
    analyze-perf.exec = "lighthouse http://localhost:3000 --view";
    db-push.exec = "cd app/client && bun run db:push";
    db-studio.exec = "cd app/client && bun run db:studio";
    server-start.exec = "cd app/server && docker-compose up -d";
    server-stop.exec = "cd app/server && docker-compose down";
    server-logs.exec = "cd app/server && docker-compose logs -f";
    server-status.exec = "cd app/server && docker-compose ps";
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

          Choose the right database for each use case and explain your reasoning.
        '';
      };

      devops-engineer = {
        description = "Service management, containers, and deployment specialist";
        proactive = false;
        tools = [ "Read" "Write" "Bash" ];
        prompt = ''
          You handle infrastructure and deployment for the Bunny project.

          Environment management:
          - devenv.nix for local development services
          - Docker Compose for production orchestration
          - Multi-stage Dockerfiles for Bun applications
          - Environment variable management (.env files, devenv env)

          Tasks:
          - Service configuration and troubleshooting
          - Container optimization (multi-stage builds, Alpine images)
          - Port management and conflict resolution
          - Health checks and monitoring
          - OTEL tracing configuration

          Always test changes with 'devenv up' before committing.
        '';
      };
    };

    commands = {
      dev-all = ''
        Start all development services (MySQL, Valkey, MinIO, Neo4j, OTEL, Next.js, Yjs)
        ```bash
        devenv up
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
    echo "Services managed by devenv:"
    echo "  MySQL (bunny_auth)     - localhost:3306"
    echo "  Valkey (cache)         - localhost:6379"
    echo "  MinIO (storage)        - localhost:9000"
    echo "  Neo4j (graph)          - bolt://localhost:7687 (http://localhost:7474)"
    echo "  OpenTelemetry          - localhost:4318"
    echo ""
    echo "Available commands:"
    echo "  build-stack     - Build Next.js app"
    echo "  test-stack      - Run unit tests"
    echo "  e2e             - Run E2E tests"
    echo "  analyze-perf    - Lighthouse audit"
    echo "  db-push         - Push MySQL schema"
    echo "  db-studio       - Open Drizzle Studio"
    echo ""
    echo "GraphQL Server commands:"
    echo "  server-start    - Start GraphQL server (Docker)"
    echo "  server-stop     - Stop GraphQL server"
    echo "  server-logs     - View server logs"
    echo "  server-status   - Check server status"
    echo ""
    echo "Run 'devenv up' to start all services"
    echo ""
    if [ ! -d "app/client/node_modules" ]; then
      echo "Installing client dependencies..."
      (cd app/client && bun install)
    fi
  '';

}
