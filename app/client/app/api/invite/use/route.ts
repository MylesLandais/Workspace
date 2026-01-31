import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { inviteCode } from "@/lib/db/schema/mysql-auth";
import { eq } from "drizzle-orm";

interface UseInviteRequest {
  code: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: UseInviteRequest = await request.json();

    if (!body.code) {
      return NextResponse.json({ error: "Code is required" }, { status: 400 });
    }

    const normalizedCode = body.code.toUpperCase().trim();

    const codeEntry = await db
      .select()
      .from(inviteCode)
      .where(eq(inviteCode.code, normalizedCode))
      .limit(1);

    if (codeEntry.length === 0) {
      return NextResponse.json(
        { error: "Invalid invite code" },
        { status: 404 },
      );
    }

    const invite = codeEntry[0];

    await db
      .update(inviteCode)
      .set({
        usedCount: invite.usedCount + 1,
        updatedAt: new Date(),
      })
      .where(eq(inviteCode.id, invite.id));

    return NextResponse.json({
      message: "Invite code used successfully",
      usedCount: invite.usedCount + 1,
    });
  } catch (error) {
    console.error("Invite use error:", error);
    return NextResponse.json(
      { error: "Failed to process invite code" },
      { status: 500 },
    );
  }
}
