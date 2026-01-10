{
  pkgs,
  lib,
  config,
  ...
}:
{
  # https://devenv.sh/packages/
  packages = [
    pkgs.lighthouse
    pkgs.otel-cli
  ];

  # https://devenv.sh/languages/
  languages = {
    javascript = {
      enable = true;
      bun = {
        enable = true;
        # Disable auto-install at root (monorepo uses app/client)
        install.enable = false;
      };
    };
  };

  # https://devenv.sh/services/
  services = {
    mysql = {
      enable = true;
      initialDatabases = [ { name = "app_db"; } ];
      ensureUsers = [
        {
          name = "user";
          password = "password";
          ensurePermissions = {
            "app_db.*" = "ALL PRIVILEGES";
          };
        }
      ];
    };
    # Note: devenv uses redis service (valkey API-compatible)
    redis.enable = true;
    minio = {
      enable = true;
      buckets = [ "uploads" ];
    };
    opentelemetry-collector = {
      enable = true;
      settings = {
        receivers.otlp.protocols = {
          grpc.endpoint = "0.0.0.0:4317";
          http.endpoint = "0.0.0.0:4318";
        };
        exporters.debug = { };
        service.pipelines.traces = {
          receivers = [ "otlp" ];
          exporters = [ "debug" ];
        };
      };
    };
  };

  # Environment variables
  env = {
    MYSQL_URL = "mysql://user:password@localhost/app_db";
    MINIO_ACCESS_KEY = "minioadmin";
    MINIO_SECRET_KEY = "minioadmin";
    OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318";
    OTEL_SERVICE_NAME = "bunny";
  };

  # https://devenv.sh/processes/
  processes = {
    web.exec = "cd app/client && bun run dev";
  };

  # https://devenv.sh/scripts/
  scripts = {
    build-stack.exec = "cd app/client && bun run build";
    test-stack.exec = "cd app/client && bun test";
    e2e.exec = "cd app/client && bun run test:e2e";
    analyze-perf.exec = "lighthouse http://localhost:3000 --view";
  };

  # https://devenv.sh/git-hooks/
  git-hooks.hooks = {
    nil.enable = true;
    prettier.enable = true;
    eslint.enable = true;
  };

  # Suppress dotenv hint (we use explicit env vars)
  dotenv.disableHint = true;

  enterShell = ''
    echo "Bunny dev environment ready."
    echo "Commands: build-stack, test-stack, e2e, analyze-perf"
    # Ensure dependencies are installed in client app
    if [ ! -d "app/client/node_modules" ]; then
      echo "Installing client dependencies..."
      (cd app/client && bun install)
    fi
  '';

  # See full reference at https://devenv.sh/reference/options/
}
