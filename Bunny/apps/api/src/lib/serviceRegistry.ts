import logger from "./logger.js";
import { getStorageBackend } from "../services/storage.js";
import { PresignedUrlService } from "../services/presignedUrl.js";
import { VectorSearchService } from "../services/vectorSearch.js";
import { DuplicateDetector } from "../services/duplicateDetector.js";

class ServiceRegistry {
  private static instance: ServiceRegistry;
  private cache = new Map<string, any>();

  private constructor() {}

  static getInstance(): ServiceRegistry {
    if (!ServiceRegistry.instance) {
      ServiceRegistry.instance = new ServiceRegistry();
    }
    return ServiceRegistry.instance;
  }

  get<T>(key: string, factory: () => T): T {
    if (!this.cache.has(key)) {
      logger.debug(`Initializing service: ${key}`);
      this.cache.set(key, factory());
    }
    return this.cache.get(key);
  }

  getStorage() {
    return this.get("storage", () => getStorageBackend());
  }

  getPresignedUrlService() {
    return this.get("presignedUrl", () => new PresignedUrlService());
  }

  getVectorSearchService() {
    return this.get("vectorSearch", () => new VectorSearchService());
  }

  getDuplicateDetector() {
    return this.get("duplicateDetector", () => new DuplicateDetector());
  }

  clear(): void {
    logger.info("Clearing service registry cache");
    this.cache.clear();
  }
}

export const serviceRegistry = ServiceRegistry.getInstance();

export function getStorage() {
  return serviceRegistry.getStorage();
}

export function getPresignedUrlService() {
  return serviceRegistry.getPresignedUrlService();
}

export function getVectorSearchService() {
  return serviceRegistry.getVectorSearchService();
}

export function getDuplicateDetector() {
  return serviceRegistry.getDuplicateDetector();
}
