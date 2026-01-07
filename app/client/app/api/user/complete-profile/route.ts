import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { user } from "@/lib/db/schema/mysql-auth";
import { eq } from "drizzle-orm";

interface CompleteProfileRequest {
  userId: string;
  username: string;
  inviteCode?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: CompleteProfileRequest = await request.json();

    if (!body.userId || !body.username) {
      return NextResponse.json(
        { error: "User ID and username are required" },
        { status: 400 }
      );
    }

    const normalizedUsername = body.username.toLowerCase().trim();

    if (!/^[a-z0-9_]{3,20}$/.test(normalizedUsername)) {
      return NextResponse.json(
        { error: "Username must be 3-20 characters, lowercase letters, numbers, or underscores only" },
        { status: 400 }
      );
    }

    const existingUser = await db
      .select()
      .from(user)
      .where(eq(user.username, normalizedUsername))
      .limit(1);

    if (existingUser.length > 0 && existingUser[0].id !== body.userId) {
      return NextResponse.json(
        { error: "Username is already taken" },
        { status: 400 }
      );
    }

    await db
      .update(user)
      .set({
        username: normalizedUsername,
        joinDate: new Date(),
        updatedAt: new Date(),
      })
      .where(eq(user.id, body.userId));

    if (body.inviteCode) {
      await fetch(`${request.nextUrl.origin}/api/invite/use`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: body.inviteCode }),
      });
    }

    return NextResponse.json({
      message: "Profile completed successfully",
      username: normalizedUsername,
    });
  } catch (error) {
    console.error("Complete profile error:", error);
    return NextResponse.json(
      { error: "Failed to complete profile" },
      { status: 500 }
    );
  }
}
