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
    const { verifyValkeyConnection } = await import('./valkey/client.js');
    const { verifyConnection } = await import('./neo4j/driver.js');

    try {
      await verifyConnection();
      await verifyValkeyConnection();
      res.json({ status: 'ok', services: { neo4j: 'ok', valkey: 'ok' } });
    } catch (error: any) {
      res.status(503).json({ status: 'error', message: error.message });
    }
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

