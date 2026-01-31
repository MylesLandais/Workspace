import { getStorageBackend, S3Storage } from "./storage.js";
import { UrlCacheService, UrlVariant } from "./urlCache.js";

export interface PresignedUrlResult {
  url: string;
  expiresAt: Date;
}

export interface BatchPresignedUrlResult {
  sha256: string;
  url: string;
  expiresAt: Date;
}

export class PresignedUrlService {
  private storage = getStorageBackend();
  private cache = new UrlCacheService();
  private defaultExpiresIn = 14400; // 4 hours in seconds

  async getPresignedUrl(
    sha256: string,
    mimeType: string,
    variant: UrlVariant = "full",
  ): Promise<PresignedUrlResult> {
    const cached = await this.cache.getCachedUrl(sha256, variant);
    if (cached) {
      return {
        url: cached,
        expiresAt: this.getExpirationDate(this.defaultExpiresIn),
      };
    }

    const url = await this.storage.getPresignedUrl(
      sha256,
      mimeType,
      this.defaultExpiresIn,
    );
    await this.cache.setCachedUrl(sha256, variant, url);

    return {
      url,
      expiresAt: this.getExpirationDate(this.defaultExpiresIn),
    };
  }

  async batchGetPresignedUrls(
    items: Array<{ sha256: string; mimeType: string }>,
    variant: UrlVariant = "full",
  ): Promise<BatchPresignedUrlResult[]> {
    if (items.length === 0) {
      return [];
    }

    const sha256s = items.map((item) => item.sha256);
    const cached = await this.cache.batchGetUrls(sha256s, variant);

    const results: BatchPresignedUrlResult[] = [];
    const uncachedItems: Array<{ sha256: string; mimeType: string }> = [];

    for (const item of items) {
      const cachedUrl = cached.get(item.sha256);
      if (cachedUrl) {
        results.push({
          sha256: item.sha256,
          url: cachedUrl,
          expiresAt: this.getExpirationDate(this.defaultExpiresIn),
        });
      } else {
        uncachedItems.push(item);
      }
    }

    if (uncachedItems.length > 0) {
      const newUrls = await Promise.all(
        uncachedItems.map(async (item) => {
          const url = await this.storage.getPresignedUrl(
            item.sha256,
            item.mimeType,
            this.defaultExpiresIn,
          );
          await this.cache.setCachedUrl(item.sha256, variant, url);
          return {
            sha256: item.sha256,
            url,
            expiresAt: this.getExpirationDate(this.defaultExpiresIn),
          };
        }),
      );

      results.push(...newUrls);
    }

    const sortedResults = items.map(
      (item) => results.find((r) => r.sha256 === item.sha256)!,
    );

    return sortedResults;
  }

  async invalidateUrl(sha256: string): Promise<void> {
    await this.cache.invalidateAllUrls(sha256);
  }

  private getExpirationDate(seconds: number): Date {
    return new Date(Date.now() + seconds * 1000);
  }

  isS3Storage(): boolean {
    return this.storage instanceof S3Storage;
  }
}
