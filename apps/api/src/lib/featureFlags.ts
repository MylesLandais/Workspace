/**
 * Feature Flag System
 *
 * Simple file-based feature flags with hot reload support using Bun's file watching.
 * Flags are stored in a JSON file and automatically reloaded when changed.
 */

import { join } from "node:path";
import logger from "./logger.js";

export interface Flag {
  key: string;
  description: string;
  enabled: boolean;
}

export type FlagMap = Record<string, Flag>;

let flags: FlagMap = {};
let flagsFilePath: string;
let reloadInterval: ReturnType<typeof setInterval> | null = null;

/**
 * Load flags from a JSON file
 */
export async function loadFlagsFromFile(filePath: string): Promise<void> {
  flagsFilePath = filePath;

  try {
    const file = Bun.file(filePath);
    if (await file.exists()) {
      const content = await file.text();
      const parsed = JSON.parse(content) as Record<string, Flag>;

      // Validate structure
      const validated: FlagMap = {};
      for (const [key, flag] of Object.entries(parsed)) {
        if (flag && typeof flag.enabled === "boolean") {
          validated[key] = {
            key: flag.key || key,
            description: flag.description || "",
            enabled: flag.enabled,
          };
        }
      }

      flags = validated;
      logger.info(
        `Loaded ${Object.keys(flags).length} feature flags from ${filePath}`,
      );
    } else {
      logger.warn(`Flags file not found: ${filePath}. Creating default flags.`);
      await createDefaultFlags(filePath);
    }
  } catch (error) {
    logger.error(`Error loading flags from ${filePath}:`, error);
    // Use empty flags on error to prevent crashes
    flags = {};
  }
}

/**
 * Create default flags file if it doesn't exist
 */
async function createDefaultFlags(filePath: string): Promise<void> {
  const defaultFlags: FlagMap = {
    "ops.sentry.enabled": {
      key: "ops.sentry.enabled",
      description: "Master switch to enable/disable sending data to Sentry",
      enabled: true,
    },
    "ops.sentry.debug-trigger.enabled": {
      key: "ops.sentry.debug-trigger.enabled",
      description:
        "Enable a specific route to intentionally throw an error for testing Sentry",
      enabled: false,
    },
  };

  try {
    await Bun.write(filePath, JSON.stringify(defaultFlags, null, 2));
    flags = defaultFlags;
    logger.info(`Created default flags file at ${filePath}`);
  } catch (error) {
    logger.error(`Error creating default flags file:`, error);
  }
}

/**
 * Initialize feature flags from file
 */
export async function initFeatureFlags(filePath?: string): Promise<void> {
  const path = filePath || join(process.cwd(), "flags.json");
  await loadFlagsFromFile(path);
}

/**
 * Start automatic reload of flags file
 * Uses polling with Bun since fs.watch may not work consistently
 */
export function startFlagReloader(intervalMs: number = 2000): void {
  if (reloadInterval) {
    clearInterval(reloadInterval);
  }

  if (!flagsFilePath) {
    logger.warn("Cannot start flag reloader: no flags file path set");
    return;
  }

  reloadInterval = setInterval(async () => {
    try {
      const file = Bun.file(flagsFilePath);
      if (await file.exists()) {
        const content = await file.text();
        const parsed = JSON.parse(content) as Record<string, Flag>;
        const newFlags: FlagMap = {};

        for (const [key, flag] of Object.entries(parsed)) {
          if (flag && typeof flag.enabled === "boolean") {
            newFlags[key] = {
              key: flag.key || key,
              description: flag.description || "",
              enabled: flag.enabled,
            };
          }
        }

        // Only log if flags actually changed
        const keysChanged = Object.keys(newFlags).filter(
          (key) => flags[key]?.enabled !== newFlags[key]?.enabled,
        );

        if (keysChanged.length > 0) {
          logger.info(`Feature flags updated: ${keysChanged.join(", ")}`);
        }

        flags = newFlags;
      }
    } catch (error) {
      // Silently fail on reload to avoid spam
      // Only log if it's a new error condition
    }
  }, intervalMs);

  logger.info(`Started feature flag reloader (polling every ${intervalMs}ms)`);
}

/**
 * Stop the flag reloader
 */
export function stopFlagReloader(): void {
  if (reloadInterval) {
    clearInterval(reloadInterval);
    reloadInterval = null;
  }
}

/**
 * Check if a feature flag is enabled
 * @param flagKey - The key of the flag to check
 * @param defaultValue - Default value if flag is not found (default: false)
 * @returns true if the flag is enabled, false otherwise
 */
export function isFeatureEnabled(
  flagKey: string,
  defaultValue: boolean = false,
): boolean {
  const flag = flags[flagKey];
  if (flag === undefined) {
    return defaultValue;
  }
  return flag.enabled;
}

/**
 * Get all flags (useful for debugging or attaching to error reports)
 */
export function getAllFlags(): FlagMap {
  return { ...flags };
}

/**
 * Get a specific flag
 */
export function getFlag(flagKey: string): Flag | undefined {
  return flags[flagKey];
}
