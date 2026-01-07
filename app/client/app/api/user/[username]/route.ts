import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { user } from "@/lib/db/schema/mysql-auth";
import { eq } from "drizzle-orm";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ username: string }> }
) {
  try {
    const { username } = await params;

    if (!username) {
      return NextResponse.json(
        { error: "Username is required" },
        { status: 400 }
      );
    }

    const userProfile = await db
      .select()
      .from(user)
      .where(eq(user.username, username))
      .limit(1);

    if (userProfile.length === 0) {
      return NextResponse.json(
        { error: "User not found" },
        { status: 404 }
      );
    }

    if (userProfile[0].profilePublic !== 1) {
      return NextResponse.json(
        { error: "This profile is private" },
        { status: 403 }
      );
    }

    return NextResponse.json({
      user: {
        username: userProfile[0].username,
        name: userProfile[0].name,
        bio: userProfile[0].bio,
        location: userProfile[0].location,
        website: userProfile[0].website,
        company: userProfile[0].company,
        image: userProfile[0].image,
        joinDate: userProfile[0].joinDate,
      },
    });
  } catch (error) {
    console.error("Get public profile error:", error);
    return NextResponse.json(
      { error: "Failed to fetch profile" },
      { status: 500 }
    );
  }
}
