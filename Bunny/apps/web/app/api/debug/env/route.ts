import { NextRequest, NextResponse } from "next/server";
import {
  validateEnvironment,
  checkDatabaseConnection,
  checkRedisConnection,
} from "@/lib/debug/env-validator";
import { createLogger } from "@/lib/debug/logger";

const log = createLogger("api:debug:env");

export async function GET(request: NextRequest) {
  log.info("Environment debug endpoint accessed");

  const envValidation = validateEnvironment();

  const [dbConnected, redisConnected] = await Promise.all([
    checkDatabaseConnection().catch(() => false),
    checkRedisConnection().catch(() => false),
  ]);

  const sanitizedEnv: Record<string, string> = {};
  const envVars = [
    "NODE_ENV",
    "NEXT_RUNTIME",
    "DATABASE_URL",
    "MYSQL_HOST",
    "MYSQL_USER",
    "MYSQL_DATABASE",
    "REDIS_URL",
    "BETTER_AUTH_SECRET",
    "BETTER_AUTH_URL",
    "NEXT_PUBLIC_APP_URL",
    "DEBUG",
  ];

  for (const key of envVars) {
    const value = process.env[key];
    if (value) {
      if (key.includes("SECRET") || key.includes("PASSWORD")) {
        sanitizedEnv[key] = "[REDACTED]";
      } else if (key.includes("URL") || key.includes("HOST")) {
        sanitizedEnv[key] = value.replace(/:[^:@]+@/, ":[REDACTED]@");
      } else {
        sanitizedEnv[key] = value;
      }
    } else {
      sanitizedEnv[key] = "[NOT SET]";
    }
  }

  return NextResponse.json({
    environment: {
      variables: sanitizedEnv,
      validation: {
        valid: envValidation.valid,
        missing: envValidation.missing,
        warnings: envValidation.warnings.length,
        errors: envValidation.errors.length,
      },
    },
    connectivity: {
      database: dbConnected,
      redis: redisConnected,
    },
    timestamp: new Date().toISOString(),
  });
}
