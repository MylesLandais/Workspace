import { mysqlDb as db } from "@/lib/db/mysql";
import { verification } from "@/lib/db/schema/mysql-auth";
import { eq, desc } from "drizzle-orm";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const email = searchParams.get("email");

  if (!email) {
    return NextResponse.json(
      { error: "email parameter required" },
      { status: 400 },
    );
  }

  const result = await db
    .select()
    .from(verification)
    .where(eq(verification.identifier, email))
    .orderBy(desc(verification.expiresAt))
    .limit(1);

  if (!result.length) {
    return NextResponse.json(
      { error: "No token found for email" },
      { status: 404 },
    );
  }

  const token = result[0].value;
  const resetUrl = `http://localhost:3000/auth/reset-password?token=${token}`;

  return NextResponse.json({
    email,
    token,
    resetUrl,
    expiresAt: result[0].expiresAt,
  });
}
