import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { mysqlDb as db } from "@/lib/db/mysql";
import { user } from "@/lib/db/schema/mysql-auth";
import { eq } from "drizzle-orm";

interface UpdateProfileRequest {
  name?: string;
  bio?: string;
  location?: string;
  website?: string;
  company?: string;
  image?: string;
  profilePublic?: boolean;
}

export async function GET(request: NextRequest) {
  try {
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session?.user) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    const userProfile = await db
      .select()
      .from(user)
      .where(eq(user.id, session.user.id))
      .limit(1);

    if (userProfile.length === 0) {
      return NextResponse.json(
        { error: "User not found" },
        { status: 404 }
      );
    }

    return NextResponse.json({
      user: {
        id: userProfile[0].id,
        name: userProfile[0].name,
        email: userProfile[0].email,
        username: userProfile[0].username,
        bio: userProfile[0].bio,
        location: userProfile[0].location,
        website: userProfile[0].website,
        company: userProfile[0].company,
        image: userProfile[0].image,
        profilePublic: userProfile[0].profilePublic === 1,
        joinDate: userProfile[0].joinDate,
      },
    });
  } catch (error) {
    console.error("Get profile error:", error);
    return NextResponse.json(
      { error: "Failed to fetch profile" },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session?.user) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    const body: UpdateProfileRequest = await request.json();

    if (body.website && !body.website.match(/^https?:\/\/.+/)) {
      return NextResponse.json(
        { error: "Website must be a valid URL starting with http:// or https://" },
        { status: 400 }
      );
    }

    await db
      .update(user)
      .set({
        name: body.name,
        bio: body.bio,
        location: body.location,
        website: body.website,
        company: body.company,
        image: body.image,
        profilePublic: body.profilePublic !== undefined ? (body.profilePublic ? 1 : 0) : undefined,
        updatedAt: new Date(),
      })
      .where(eq(user.id, session.user.id));

    return NextResponse.json({
      message: "Profile updated successfully",
    });
  } catch (error) {
    console.error("Update profile error:", error);
    return NextResponse.json(
      { error: "Failed to update profile" },
      { status: 500 }
    );
  }
}
