import { getSession as getNeo4jSession, Session } from 'neo4j-driver';
import { driver } from '../neo4j/driver.js';
import logger from './logger.js';

export async function withSession<T>(
  callback: (session: Session) => Promise<T>
): Promise<T> {
  const session = driver.session();

  try {
    const result = await callback(session);
    return result;
  } catch (error) {
    logger.error('Error in Neo4j transaction', error);
    throw error;
  } finally {
    await session.close();
  }
}

export async function withTransaction<T>(
  callback: (tx: Session) => Promise<T>
): Promise<T> {
  const session = driver.session();

  try {
    const tx = session.beginTransaction();
    const result = await callback(tx);

    await tx.commit();
    return result;
  } catch (error) {
    logger.error('Error in Neo4j transaction, rolling back', error);

    try {
      await tx.rollback();
    } catch (rollbackError) {
      logger.error('Failed to rollback transaction', rollbackError);
    }

    throw error;
  } finally {
    await session.close();
  }
}
