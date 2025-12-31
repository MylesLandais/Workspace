import { createClient } from 'redis';
import dotenv from 'dotenv';

dotenv.config();

const uri = process.env.VALKEY_URI || 'redis://valkey:6379';
const password = process.env.VALKEY_PASSWORD || undefined;

let client: ReturnType<typeof createClient> | null = null;

export function getValkeyClient() {
  if (!client) {
    const url = new URL(uri);
    client = createClient({
      socket: {
        host: url.hostname,
        port: parseInt(url.port || '6379'),
      },
      password: password || undefined,
    });

    client.on('error', (err) => {
      console.error('Valkey client error:', err);
    });

    client.on('connect', () => {
      console.log('Valkey client connected');
    });

    client.connect().catch((err) => {
      console.error('Failed to connect to Valkey:', err);
    });
  }
  return client;
}

export async function verifyValkeyConnection() {
  const client = getValkeyClient();
  try {
    await client.ping();
    console.log('Valkey connection verified');
    return true;
  } catch (error) {
    console.error('Failed to connect to Valkey:', error);
    throw error;
  }
}

export async function closeValkeyConnection() {
  if (client) {
    await client.quit();
    client = null;
  }
}

