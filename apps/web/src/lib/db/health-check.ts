/**
 * Database Health Check Utility
 *
 * Provides diagnostics for database connectivity and sends warnings to Sentry.
 */
import * as Sentry from "@sentry/nextjs";
import { pool } from "./mysql";

interface HealthCheckResult {
  status: "healthy" | "degraded" | "unhealthy";
  poolStats: {
    connectionCount: number;
    queueLength: number;
  };
  error?: string;
  timestamp: string;
}

/**
 * Check database connection pool health
 */
export async function checkDatabaseHealth(): Promise<HealthCheckResult> {
  const timestamp = new Date().toISOString();

  try {
    // Get pool statistics
    const poolStats = pool.pool;
    const connectionCount = poolStats?._allConnections?.length || 0;
    const queueLength = poolStats?._connectionQueue?.length || 0;

    // Try a simple query
    try {
      const connection = await pool.getConnection();
      await connection.ping();
      connection.release();

      return {
        status: "healthy",
        poolStats: {
          connectionCount,
          queueLength,
        },
        timestamp,
      };
    } catch (queryError) {
      const errorMessage =
        queryError instanceof Error ? queryError.message : String(queryError);

      // Report to Sentry as warning
      Sentry.captureMessage("Database ping failed", {
        level: "warning",
        tags: {
          health_check: "database_ping",
          error_type: "database_ping_failed",
        },
        extra: {
          error: errorMessage,
          poolStats: {
            connectionCount,
            queueLength,
          },
          timestamp,
        },
        contexts: {
          database_health: {
            status: "degraded",
            error: errorMessage,
            poolStats: {
              connectionCount,
              queueLength,
            },
          },
        },
      });

      return {
        status: "degraded",
        poolStats: {
          connectionCount,
          queueLength,
        },
        error: errorMessage,
        timestamp,
      };
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);

    // Report to Sentry as error
    Sentry.captureException(error, {
      tags: {
        health_check: "database_health",
        error_type: "database_connection_check_failed",
      },
      level: "error",
      contexts: {
        database_health: {
          status: "unhealthy",
          error: errorMessage,
        },
      },
    });

    return {
      status: "unhealthy",
      poolStats: {
        connectionCount: 0,
        queueLength: 0,
      },
      error: errorMessage,
      timestamp,
    };
  }
}

/**
 * Middleware to check database health and warn about issues
 */
export async function withDatabaseHealthCheck<T>(
  operation: () => Promise<T>,
  operationName: string = "database_operation",
): Promise<T> {
  try {
    // Quick health check
    const health = await checkDatabaseHealth();

    if (health.status === "unhealthy") {
      Sentry.captureMessage(`Database unhealthy during ${operationName}`, {
        level: "error",
        tags: {
          operation: operationName,
          "database.status": "unhealthy",
        },
        extra: {
          health,
        },
        contexts: {
          database_operation: {
            name: operationName,
            health,
          },
        },
      });

      console.error(
        `[Database] Unhealthy during ${operationName}:`,
        health.error,
      );
    } else if (health.status === "degraded") {
      console.warn(
        `[Database] Degraded during ${operationName}:`,
        health.error,
      );
    }

    // Execute the operation
    return await operation();
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);

    // Report operation failure to Sentry
    Sentry.captureException(error, {
      tags: {
        operation: operationName,
        "error.context": "database_operation",
      },
      extra: {
        operationName,
        errorMessage,
      },
      contexts: {
        database_operation: {
          name: operationName,
          failed: true,
          error: errorMessage,
        },
      },
    });

    throw error;
  }
}
