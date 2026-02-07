/**
 * Centralized Debug Logger
 *
 * Provides structured logging with multiple levels and namespace support.
 * Respects DEBUG environment variable for filtering logs.
 *
 * Usage:
 *   const log = createLogger('auth');
 *   log.debug('Session loaded', { userId: 123 });
 *   log.error('Auth failed', error);
 *
 * Environment:
 *   DEBUG=* - Enable all logs
 *   DEBUG=auth:* - Enable auth namespace
 *   DEBUG=api:* - Enable API logs
 */

type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

interface LogContext {
  [key: string]: unknown;
}

class Logger {
  private namespace: string;
  private debugEnabled: boolean;

  constructor(namespace: string) {
    this.namespace = namespace;
    this.debugEnabled = this.shouldEnableDebug();
  }

  private shouldEnableDebug(): boolean {
    try {
      if (typeof process === "undefined") return false;

      const debugEnv = process.env.DEBUG || process.env.NEXT_PUBLIC_DEBUG || "";
      if (debugEnv === "*") return true;
      if (debugEnv === "false" || debugEnv === "0") return false;

      const patterns = debugEnv.split(",").map((p) => p.trim());
      return patterns.some((pattern) => {
        if (pattern === "*") return true;
        if (pattern.endsWith(":*")) {
          const prefix = pattern.slice(0, -2);
          return this.namespace.startsWith(prefix);
        }
        return this.namespace === pattern;
      });
    } catch {
      return false;
    }
  }

  private shouldLog(level: LogLevel): boolean {
    try {
      if (typeof process !== "undefined" && process.env.NODE_ENV === "test") {
        return false;
      }
    } catch {
      // If we can't access process, continue
    }

    if (level === "ERROR" || level === "WARN") return true;
    if (level === "INFO") return this.debugEnabled;
    if (level === "DEBUG") return this.debugEnabled;
    return false;
  }

  private formatMessage(
    level: LogLevel,
    message: string,
    context?: LogContext,
  ): string {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level}] [${this.namespace}]`;

    if (context && Object.keys(context).length > 0) {
      return `${prefix} ${message} ${JSON.stringify(context)}`;
    }
    return `${prefix} ${message}`;
  }

  debug(message: string, context?: LogContext): void {
    if (!this.shouldLog("DEBUG")) return;
    console.debug(this.formatMessage("DEBUG", message, context));
  }

  info(message: string, context?: LogContext): void {
    if (!this.shouldLog("INFO")) return;
    console.info(this.formatMessage("INFO", message, context));
  }

  warn(message: string, context?: LogContext): void {
    if (!this.shouldLog("WARN")) return;
    console.warn(this.formatMessage("WARN", message, context));
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
    if (!this.shouldLog("ERROR")) return;

    const errorDetails =
      error instanceof Error
        ? {
            message: error.message,
            stack: error.stack,
            name: error.name,
          }
        : { error };

    console.error(
      this.formatMessage("ERROR", message, { ...context, ...errorDetails }),
    );
  }

  time(label: string): void {
    if (!this.debugEnabled) return;
    console.time(`[${this.namespace}] ${label}`);
  }

  timeEnd(label: string): void {
    if (!this.debugEnabled) return;
    console.timeEnd(`[${this.namespace}] ${label}`);
  }
}

const loggers = new Map<string, Logger>();

export function createLogger(namespace: string): Logger {
  if (!loggers.has(namespace)) {
    loggers.set(namespace, new Logger(namespace));
  }
  return loggers.get(namespace)!;
}

export const logger = createLogger("app");
