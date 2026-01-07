import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { inviteCode } from "@/lib/db/schema/mysql-auth";
import { v4 as uuidv4 } from "uuid";

interface GenerateInviteRequest {
  code?: string;
  expiresInDays?: number;
  maxUses?: number;
  notes?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: GenerateInviteRequest = await request.json();

    const generatedCode = body.code || `SN-${uuidv4().slice(0, 8).toUpperCase()}`;
    const normalizedCode = generatedCode.toUpperCase().trim();

    const expiresInDays = body.expiresInDays || 365;
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + expiresInDays);

    const id = uuidv4();
    await db.insert(inviteCode).values({
      id,
      code: normalizedCode,
      expiresAt,
      maxUses: body.maxUses || null,
      usedCount: 0,
      notes: body.notes || null,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    return NextResponse.json(
      {
        message: "Invite code generated successfully",
        code: normalizedCode,
        expiresAt,
        maxUses: body.maxUses,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Invite generation error:", error);
    return NextResponse.json(
      { error: "Failed to generate invite code" },
      { status: 500 }
    );
  }
}
