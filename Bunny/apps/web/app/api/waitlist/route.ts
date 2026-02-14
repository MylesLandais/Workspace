import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { waitlist } from "@/lib/db/schema/mysql-auth";
import { v4 as uuidv4 } from "uuid";
import { eq } from "drizzle-orm";
import {
  withApiLogging,
  logDatabaseQuery,
  logDatabaseResult,
} from "@/lib/debug/api-logger";
import { createLogger } from "@/lib/debug/logger";

const log = createLogger("api:waitlist");

interface WaitlistRequest {
  email: string;
  name?: string;
  source?: string;
}

export async function POST(request: NextRequest) {
  return withApiLogging<Record<string, unknown>>(request, async () => {
    const body: WaitlistRequest = await request.json();

    log.debug("Waitlist submission received", {
      hasEmail: !!body.email,
      hasName: !!body.name,
      source: body.source,
    });

    if (!body.email) {
      log.warn("Waitlist submission missing email");
      return NextResponse.json({ error: "Email is required" }, { status: 400 });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.email)) {
      log.warn("Invalid email format", {
        email: body.email.substring(0, 5) + "...",
      });
      return NextResponse.json(
        { error: "Invalid email format" },
        { status: 400 },
      );
    }

    logDatabaseQuery("SELECT FROM waitlist WHERE email = ?", [body.email]);
    const existingEntry = await db
      .select()
      .from(waitlist)
      .where(eq(waitlist.email, body.email))
      .limit(1);
    logDatabaseResult(existingEntry.length);

    if (existingEntry.length > 0) {
      log.info("Email already on waitlist", {
        status: existingEntry[0].status,
      });
      return NextResponse.json(
        {
          message: "You are already on the waitlist",
          status: existingEntry[0].status,
        },
        { status: 200 },
      );
    }

    const id = uuidv4();
    logDatabaseQuery("INSERT INTO waitlist VALUES (...)", [id, body.email]);
    await db.insert(waitlist).values({
      id,
      email: body.email,
      name: body.name || null,
      source: body.source || "website",
      status: "pending",
      createdAt: new Date(),
      updatedAt: new Date(),
    });
    logDatabaseResult(1);

    log.info("Successfully added to waitlist", { id, source: body.source });
    return NextResponse.json(
      {
        message: "Successfully joined the waitlist",
        id,
      },
      { status: 201 },
    );
  });
}

export async function GET(request: NextRequest) {
  return withApiLogging<Record<string, unknown>>(request, async () => {
    const email = request.nextUrl.searchParams.get("email");

    log.debug("Waitlist lookup request", { hasEmail: !!email });

    if (!email) {
      log.warn("Waitlist lookup missing email parameter");
      return NextResponse.json(
        { error: "Email parameter is required" },
        { status: 400 },
      );
    }

    logDatabaseQuery("SELECT FROM waitlist WHERE email = ?", [email]);
    const entry = await db
      .select()
      .from(waitlist)
      .where(eq(waitlist.email, email))
      .limit(1);
    logDatabaseResult(entry.length);

    if (entry.length === 0) {
      log.info("Email not found on waitlist");
      return NextResponse.json(
        { message: "Email not found on waitlist", status: null },
        { status: 404 },
      );
    }

    log.info("Waitlist entry found", { status: entry[0].status });
    return NextResponse.json({
      email: entry[0].email,
      name: entry[0].name,
      status: entry[0].status,
      createdAt: entry[0].createdAt,
    });
  });
}
