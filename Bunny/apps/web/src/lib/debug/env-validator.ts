/**
 * Environment Variable Validator
 *
 * Validates required environment variables on application startup.
 * Logs detailed information about missing or invalid configuration.
 */

import { createLogger } from "./logger";

const log = createLogger("env");

export interface EnvValidationResult {
  valid: boolean;
  missing: string[];
  warnings: string[];
  errors: string[];
}

interface EnvVarConfig {
  key: string;
  required: boolean;
  description: string;
  validate?: (value: string) => boolean;
}

const ENV_VARS: EnvVarConfig[] = [
  {
    key: "DATABASE_URL",
    required: false,
    description:
      "PostgreSQL database connection URL (optional, uses MySQL if not set)",
  },
  {
    key: "MYSQL_HOST",
    required: false,
    description: "MySQL database host (defaults to localhost)",
  },
  {
    key: "MYSQL_USER",
    required: false,
    description: "MySQL database user (defaults to root)",
  },
  {
    key: "MYSQL_PASSWORD",
    required: false,
    description: "MySQL database password",
  },
  {
    key: "MYSQL_DATABASE",
    required: false,
    description: "MySQL database name (defaults to bunny_auth)",
  },
  {
    key: "REDIS_URL",
    required: false,
    description: "Redis connection URL (defaults to redis://localhost:6379)",
  },
  {
    key: "BETTER_AUTH_SECRET",
    required: false,
    description: "Secret key for Better Auth (uses default in dev)",
  },
  {
    key: "BETTER_AUTH_URL",
    required: false,
    description: "Base URL for Better Auth (defaults to http://localhost:3000)",
  },
  {
    key: "NEXT_PUBLIC_APP_URL",
    required: false,
    description: "Public app URL for client-side",
  },
  {
    key: "NODE_ENV",
    required: true,
    description: "Node environment (development, production, test)",
    validate: (value) => ["development", "production", "test"].includes(value),
  },
];

export function validateEnvironment(): EnvValidationResult {
  const result: EnvValidationResult = {
    valid: true,
    missing: [],
    warnings: [],
    errors: [],
  };

  log.debug("Validating environment variables...");

  for (const config of ENV_VARS) {
    const value = process.env[config.key];

    if (!value) {
      if (config.required) {
        result.valid = false;
        result.missing.push(config.key);
        result.errors.push(
          `Missing required environment variable: ${config.key} - ${config.description}`,
        );
        log.error(`Missing required: ${config.key}`, undefined, {
          description: config.description,
        });
      } else {
        result.warnings.push(
          `Optional environment variable not set: ${config.key} - ${config.description}`,
        );
        log.debug(`Optional not set: ${config.key}`, {
          description: config.description,
        });
      }
    } else {
      if (config.validate && !config.validate(value)) {
        result.valid = false;
        result.errors.push(
          `Invalid value for ${config.key}: ${value} - ${config.description}`,
        );
        log.error(`Invalid value: ${config.key}`, undefined, { value });
      } else {
        log.debug(`Valid: ${config.key}`, {
          hasValue: true,
          length: value.length,
        });
      }
    }
  }

  if (result.valid) {
    log.info("Environment validation passed", {
      totalChecked: ENV_VARS.length,
      warnings: result.warnings.length,
    });
  } else {
    log.error("Environment validation failed", undefined, {
      missing: result.missing,
      errors: result.errors.length,
    });
  }

  return result;
}

export function logEnvironmentSummary(): void {
  log.info("Environment Summary", {
    nodeEnv: process.env.NODE_ENV,
    nextRuntime: process.env.NEXT_RUNTIME,
    debugEnabled: process.env.DEBUG || "none",
    hasDatabase: !!(process.env.DATABASE_URL || process.env.MYSQL_HOST),
    hasRedis: !!process.env.REDIS_URL,
    hasAuth: !!process.env.BETTER_AUTH_SECRET,
  });
}

export async function checkDatabaseConnection(): Promise<boolean> {
  try {
    log.debug("Checking database connection...");

    const { mysqlDb } = await import("../db/mysql");
    const result = await Promise.race([
      mysqlDb.execute("SELECT 1"),
      new Promise((_, reject) =>
        setTimeout(
          () => reject(new Error("Database connection timeout")),
          5000,
        ),
      ),
    ]);

    log.info("Database connection successful");
    return true;
  } catch (error) {
    log.warn("Database connection check failed (this is OK during startup)", {
      error: error instanceof Error ? error.message : "Unknown error",
    });
    return false;
  }
}

export async function checkRedisConnection(): Promise<boolean> {
  try {
    log.debug("Checking Redis connection...");

    const Redis = (await import("ioredis")).default;
    const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379", {
      connectTimeout: 5000,
      maxRetriesPerRequest: 1,
      lazyConnect: true,
    });

    await Promise.race([
      redis.connect().then(() => redis.ping()),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Redis connection timeout")), 5000),
      ),
    ]);

    await redis.quit();

    log.info("Redis connection successful");
    return true;
  } catch (error) {
    log.warn("Redis connection check failed (this is OK during startup)", {
      error: error instanceof Error ? error.message : "Unknown error",
    });
    return false;
  }
}

export async function runStartupChecks(): Promise<void> {
  log.info("Running startup checks...");

  const envResult = validateEnvironment();
  logEnvironmentSummary();

  if (!envResult.valid) {
    log.warn("Environment validation failed, continuing with defaults");
  }

  const dbOk = await checkDatabaseConnection();
  const redisOk = await checkRedisConnection();

  log.info("Startup checks complete", {
    environment: envResult.valid ? "valid" : "using defaults",
    database: dbOk ? "connected" : "failed",
    redis: redisOk ? "connected" : "failed",
  });
}
