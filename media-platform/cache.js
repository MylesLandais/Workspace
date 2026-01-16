const { createClient } = require('redis');
const config = require('./config');

class Cache {
  constructor() {
    this.client = null;
    this.isConnected = false;
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0
    };
  }

  async connect() {
    try {
      const url = config.valkey.url.replace('valkey://', 'redis://');
      this.client = createClient({
        url: url,
        password: config.valkey.password,
        database: config.valkey.db
      });

      this.client.on('error', (err) => {
        console.error('Valkey Client Error:', err);
        this.isConnected = false;
      });

      this.client.on('connect', () => {
        console.log('Valkey connecting...');
      });

      this.client.on('ready', () => {
        console.log('Valkey ready');
        this.isConnected = true;
      });

      await this.client.connect();
    } catch (error) {
      console.error('Failed to connect to Valkey:', error);
      throw error;
    }
  }

  async disconnect() {
    if (this.client) {
      await this.client.quit();
      this.isConnected = false;
    }
  }

  async get(key) {
    try {
      const value = await this.client.get(key);
      if (value !== null) {
        this.stats.hits++;
        return JSON.parse(value);
      } else {
        this.stats.misses++;
        return null;
      }
    } catch (error) {
      console.error('Cache get error:', error);
      this.stats.misses++;
      return null;
    }
  }

  async set(key, value, ttl = null) {
    try {
      const serialized = JSON.stringify(value);
      if (ttl) {
        await this.client.setEx(key, ttl, serialized);
      } else {
        await this.client.set(key, serialized);
      }
      this.stats.sets++;
      return true;
    } catch (error) {
      console.error('Cache set error:', error);
      return false;
    }
  }

  async delete(key) {
    try {
      await this.client.del(key);
      this.stats.deletes++;
      return true;
    } catch (error) {
      console.error('Cache delete error:', error);
      return false;
    }
  }

  async flushAll() {
    try {
      await this.client.flushAll();
      this.stats = { hits: 0, misses: 0, sets: 0, deletes: 0 };
      return true;
    } catch (error) {
      console.error('Cache flush error:', error);
      return false;
    }
  }

  async info() {
    try {
      return await this.client.info();
    } catch (error) {
      console.error('Cache info error:', error);
      return null;
    }
  }

  getStats() {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? (this.stats.hits / total * 100).toFixed(2) : 0;
    
    return {
      ...this.stats,
      total,
      hitRate: `${hitRate}%`
    };
  }
}

const cache = new Cache();

module.exports = { cache };




