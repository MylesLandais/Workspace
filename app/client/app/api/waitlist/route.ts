import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { waitlist } from "@/lib/db/schema/mysql-auth";
import { v4 as uuidv4 } from "uuid";
import { eq } from "drizzle-orm";

interface WaitlistRequest {
  email: string;
  name?: string;
  source?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: WaitlistRequest = await request.json();

    if (!body.email) {
      return NextResponse.json(
        { error: "Email is required" },
        { status: 400 }
      );
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.email)) {
      return NextResponse.json(
        { error: "Invalid email format" },
        { status: 400 }
      );
    }

    const existingEntry = await db
      .select()
      .from(waitlist)
      .where(eq(waitlist.email, body.email))
      .limit(1);

    if (existingEntry.length > 0) {
      return NextResponse.json(
        {
          message: "You are already on the waitlist",
          status: existingEntry[0].status,
        },
        { status: 200 }
      );
    }

    const id = uuidv4();
    await db.insert(waitlist).values({
      id,
      email: body.email,
      name: body.name || null,
      source: body.source || "website",
      status: "pending",
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    return NextResponse.json(
      {
        message: "Successfully joined the waitlist",
        id,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Waitlist submission error:", error);
    return NextResponse.json(
      { error: "Failed to process request" },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const email = request.nextUrl.searchParams.get("email");

    if (!email) {
      return NextResponse.json(
        { error: "Email parameter is required" },
        { status: 400 }
      );
    }

    const entry = await db
      .select()
      .from(waitlist)
      .where(eq(waitlist.email, email))
      .limit(1);

    if (entry.length === 0) {
      return NextResponse.json(
        { message: "Email not found on waitlist", status: null },
        { status: 404 }
      );
    }

    return NextResponse.json({
      email: entry[0].email,
      name: entry[0].name,
      status: entry[0].status,
      createdAt: entry[0].createdAt,
    });
  } catch (error) {
    console.error("Waitlist lookup error:", error);
    return NextResponse.json(
      { error: "Failed to process request" },
      { status: 500 }
    );
  }
}
