import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { inviteCode } from "@/lib/db/schema/mysql-auth";
import { eq } from "drizzle-orm";

export async function GET(request: NextRequest) {
  try {
    const code = request.nextUrl.searchParams.get("code");

    if (!code) {
      return NextResponse.json(
        { error: "Code parameter is required", valid: false },
        { status: 400 },
      );
    }

    const normalizedCode = code.toUpperCase().trim();

    const codeEntry = await db
      .select()
      .from(inviteCode)
      .where(eq(inviteCode.code, normalizedCode))
      .limit(1);

    if (codeEntry.length === 0) {
      return NextResponse.json(
        { valid: false, message: "Invalid invite code" },
        { status: 404 },
      );
    }

    const invite = codeEntry[0];
    const now = new Date();

    if (invite.expiresAt && invite.expiresAt < now) {
      return NextResponse.json(
        { valid: false, message: "Invite code has expired" },
        { status: 400 },
      );
    }

    if (invite.maxUses && invite.usedCount >= invite.maxUses) {
      return NextResponse.json(
        { valid: false, message: "Invite code has reached maximum uses" },
        { status: 400 },
      );
    }

    return NextResponse.json({
      valid: true,
      code: invite.code,
      expiresAt: invite.expiresAt,
      message: "Invite code is valid",
    });
  } catch (error) {
    console.error("Invite validation error:", error);
    return NextResponse.json(
      { error: "Failed to validate invite code", valid: false },
      { status: 500 },
    );
  }
}
