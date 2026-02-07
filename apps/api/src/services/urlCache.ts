import { getValkeyClient } from "../valkey/client.js";

export type UrlVariant = "full" | "thumb";

export class UrlCacheService {
  private client = getValkeyClient();
  private ttl = 12600; // 3.5 hours in seconds

  async getCachedUrl(
    sha256: string,
    variant: UrlVariant,
  ): Promise<string | null> {
    const key = `presigned:${sha256}:${variant}`;
    return await this.client.get(key);
  }

  async setCachedUrl(
    sha256: string,
    variant: UrlVariant,
    url: string,
  ): Promise<void> {
    const key = `presigned:${sha256}:${variant}`;
    await this.client.setEx(key, this.ttl, url);
  }

  async batchGetUrls(
    sha256s: string[],
    variant: UrlVariant,
  ): Promise<Map<string, string | null>> {
    if (sha256s.length === 0) {
      return new Map();
    }

    const keys = sha256s.map((sha) => `presigned:${sha}:${variant}`);
    const values = await this.client.mGet(keys);

    const result = new Map<string, string | null>();
    sha256s.forEach((sha, i) => {
      result.set(sha, values[i]);
    });

    return result;
  }

  async invalidateUrl(sha256: string, variant: UrlVariant): Promise<void> {
    const key = `presigned:${sha256}:${variant}`;
    await this.client.del(key);
  }

  async invalidateAllUrls(sha256: string): Promise<void> {
    await Promise.all([
      this.invalidateUrl(sha256, "full"),
      this.invalidateUrl(sha256, "thumb"),
    ]);
  }
}
