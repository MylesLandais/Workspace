import express from 'express';
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import cors from 'cors';
import { typeDefs } from './schema/schema.js';
import { queryResolvers } from './resolvers/queries.js';
import { mutationResolvers } from './resolvers/mutations.js';
import { bunnyResolvers } from './bunny/resolvers.js';
import { verifyConnection, createIndexes } from './neo4j/driver.js';
import { verifyValkeyConnection } from './valkey/client.js';
import logger from './lib/logger.js';
import { errorHandler, notFoundHandler, formatError } from './lib/errorHandler.js';

export interface Context {
  req: express.Request;
}

const PORT = process.env.PORT || 4002;

async function startServer() {
  try {
    await verifyConnection();
    await createIndexes();
    await verifyValkeyConnection();
  } catch (error) {
    logger.error('Failed to initialize services', error);
    process.exit(1);
  }

  const app = express();

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
    '/api/graphql',
    cors(),
    express.json({ limit: '10mb' }),
    expressMiddleware(server, {
      context: async ({ req }) => ({ req }),
    })
  );

  app.get('/health', async (req, res) => {
    const startTime = Date.now();
    const { verifyValkeyConnection } = await import('./valkey/client.js');
    const { verifyConnection } = await import('./neo4j/driver.js');

    const checks: Record<string, { status: string; error?: string }> = {
      neo4j: { status: 'unknown' },
      valkey: { status: 'unknown' },
    };

    try {
      await verifyConnection();
      checks.neo4j.status = 'healthy';
    } catch (error: any) {
      checks.neo4j.status = 'unhealthy';
      checks.neo4j.error = error.message;
    }

    try {
      await verifyValkeyConnection();
      checks.valkey.status = 'healthy';
    } catch (error: any) {
      checks.valkey.status = 'unhealthy';
      checks.valkey.error = error.message;
    }

    const responseTime = Date.now() - startTime;
    const allHealthy = Object.values(checks).every(c => c.status === 'healthy');

    res.status(allHealthy ? 200 : 503).json({
      status: allHealthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      responseTime,
      checks,
    });
  });

  // Error handling middleware (must be after all routes)
  app.use(notFoundHandler);
  app.use(errorHandler);

  app.listen(PORT, () => {
    logger.info(`Server running on http://localhost:${PORT}`);
    logger.info(`GraphQL endpoint: http://localhost:${PORT}/api/graphql`);
  });
}

startServer().catch((error) => {
  logger.error('Failed to start server', error);
  process.exit(1);
});

