import * as Sentry from "@sentry/bun";
import express from "express";
import { ApolloServer } from "@apollo/server";
import { expressMiddleware } from "@apollo/server/express4";
import cors from "cors";
import { typeDefs } from "./schema/schema.js";
import { queryResolvers } from "./resolvers/queries.js";
import { mutationResolvers } from "./resolvers/mutations.js";
import { bunnyResolvers } from "./bunny/resolvers.js";
import { verifyConnection, createIndexes } from "./neo4j/driver.js";
import { verifyValkeyConnection } from "./valkey/client.js";
import logger from "./lib/logger.js";
import {
  errorHandler,
  notFoundHandler,
  formatError,
} from "./lib/errorHandler.js";
import {
  initFeatureFlags,
  startFlagReloader,
  isFeatureEnabled,
} from "./lib/featureFlags.js";
import { initSentry, captureException } from "./lib/sentryHelper.js";

export interface Context {
  req: express.Request;
}

const PORT = process.env.PORT || 4002;

async function startServer() {
  // 1. Initialize Feature Flags first
  await initFeatureFlags();
  startFlagReloader();

  // 2. Initialize Sentry with feature flag support
  initSentry();

  try {
    await verifyConnection();
    await createIndexes();
    await verifyValkeyConnection();
  } catch (error) {
    logger.error("Failed to initialize services", error);
    captureException(error);
    process.exit(1);
  }

  const app = express();

  // Add Sentry error handler middleware
  // TODO: Fix Sentry.Handlers API for @sentry/bun SDK
  // if (process.env.SENTRY_DSN || isFeatureEnabled("ops.sentry.enabled", true)) {
  //   app.use(Sentry.Handlers.requestHandler());
  //   app.use(Sentry.Handlers.errorHandler());
  // }

  const server = new ApolloServer({
    typeDefs,
    resolvers: {
      Query: {
        ...queryResolvers.Query,
        ...bunnyResolvers.Query,
      },
      Mutation: {
        ...mutationResolvers.Mutation,
        ...bunnyResolvers.Mutation,
      },
    },
    formatError,
  });

  await server.start();

  app.use(
    "/api/graphql",
    cors(),
    express.json({ limit: "10mb" }),
    expressMiddleware(server, {
      context: async ({ req }) => ({ req }),
    }),
  );

  app.get("/health", async (req, res) => {
    const startTime = Date.now();
    const { verifyValkeyConnection } = await import("./valkey/client.js");
    const { verifyConnection } = await import("./neo4j/driver.js");

    const checks: Record<string, { status: string; error?: string }> = {
      neo4j: { status: "unknown" },
      valkey: { status: "unknown" },
    };

    try {
      await verifyConnection();
      checks.neo4j.status = "healthy";
    } catch (error: any) {
      checks.neo4j.status = "unhealthy";
      checks.neo4j.error = error.message;
    }

    try {
      await verifyValkeyConnection();
      checks.valkey.status = "healthy";
    } catch (error: any) {
      checks.valkey.status = "unhealthy";
      checks.valkey.error = error.message;
    }

    const responseTime = Date.now() - startTime;
    const allHealthy = Object.values(checks).every(
      (c) => c.status === "healthy",
    );

    res.status(allHealthy ? 200 : 503).json({
      status: allHealthy ? "healthy" : "degraded",
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      responseTime,
      checks,
    });
  });

  // Sentry test endpoint (legacy - kept for backward compatibility)
  app.get("/test-sentry", (req, res) => {
    try {
      throw new Error("Sentry Bun test");
    } catch (e) {
      captureException(e);
      res.json({
        status: "test_error_captured",
        message: "Intentional test error sent to Sentry",
        error: (e as Error).message,
      });
    }
  });

  // --- SENTRY INTEGRATION TEST PATTERN ---
  // Debug trigger endpoint protected by feature flag
  app.get("/debug-error", (req, res) => {
    // 1. Check if we are allowed to run this test
    if (isFeatureEnabled("ops.sentry.debug-trigger.enabled", false)) {
      try {
        // 2. Intentionally throw
        throw new Error(`Manual Sentry Test at ${new Date().toISOString()}`);
      } catch (e) {
        // 3. Capture it with context
        captureException(e, {
          tags: {
            test_endpoint: "debug-error",
            triggered_by: "manual",
          },
          extra: {
            url: req.url,
            method: req.method,
            headers: req.headers,
          },
        });
        res.status(500).json({
          status: "error_sent_to_sentry",
          message: "Error sent to Sentry.",
          error: (e as Error).message,
          timestamp: new Date().toISOString(),
        });
      }
    } else {
      // Hide the existence of this route if flag is disabled
      res.status(404).json({
        status: "not_found",
        message: "Not Found",
      });
    }
  });
  // ---------------------------------------

  // Error handling middleware (must be after all routes)
  app.use(notFoundHandler);
  app.use(errorHandler);

  app.listen(PORT, () => {
    logger.info(`Server running on http://localhost:${PORT}`);
    logger.info(`GraphQL endpoint: http://localhost:${PORT}/api/graphql`);
  });
}

startServer().catch((error) => {
  logger.error("Failed to start server", error);
  captureException(error, {
    tags: {
      error_type: "server_startup_failure",
    },
  });
  process.exit(1);
});
