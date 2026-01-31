import { NextRequest, NextResponse } from "next/server";
import { mysqlDb as db } from "@/lib/db/mysql";
import { user } from "@/lib/db/schema/mysql-auth";
import { eq } from "drizzle-orm";
import { withSpan, addSpanEvent } from "@/lib/tracing/tracer";

interface CompleteProfileRequest {
  userId: string;
  username: string;
  inviteCode?: string;
}

export async function POST(request: NextRequest) {
  return withSpan(
    "user.complete-profile",
    async (span) => {
      try {
        const body: CompleteProfileRequest = await request.json();

        span.setAttributes({
          "user.id": body.userId || "unknown",
          "user.has_invite": !!body.inviteCode,
          component: "user-api",
          operation: "complete-profile",
        });

        addSpanEvent(span, "profile.complete.start", {
          userId: body.userId,
          hasInvite: !!body.inviteCode,
        });

        if (!body.userId || !body.username) {
          span.setAttribute("error", true);
          span.setAttribute("error.message", "Missing required fields");
          return NextResponse.json(
            { error: "User ID and username are required" },
            { status: 400 },
          );
        }

        const normalizedUsername = body.username.toLowerCase().trim();

        span.setAttribute("user.username", normalizedUsername);

        if (!/^[a-z0-9_]{3,20}$/.test(normalizedUsername)) {
          span.setAttribute("error", true);
          span.setAttribute("error.message", "Invalid username format");
          return NextResponse.json(
            {
              error:
                "Username must be 3-20 characters, lowercase letters, numbers, or underscores only",
            },
            { status: 400 },
          );
        }

        addSpanEvent(span, "db.check-username-unique.start");
        const existingUser = await db
          .select()
          .from(user)
          .where(eq(user.username, normalizedUsername))
          .limit(1);
        addSpanEvent(span, "db.check-username-unique.complete", {
          existingCount: existingUser.length,
        });

        if (existingUser.length > 0 && existingUser[0].id !== body.userId) {
          span.setAttribute("error", true);
          span.setAttribute("error.message", "Username already taken");
          return NextResponse.json(
            { error: "Username is already taken" },
            { status: 400 },
          );
        }

        addSpanEvent(span, "db.update-user.start");
        await db
          .update(user)
          .set({
            username: normalizedUsername,
            joinDate: new Date(),
            updatedAt: new Date(),
          })
          .where(eq(user.id, body.userId));
        addSpanEvent(span, "db.update-user.complete");

        if (body.inviteCode) {
          addSpanEvent(span, "invite.use.start", {
            code: body.inviteCode,
          });
          try {
            await fetch(`${request.nextUrl.origin}/api/invite/use`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ code: body.inviteCode }),
            });
            addSpanEvent(span, "invite.use.complete");
          } catch (inviteError) {
            span.setAttribute("invite.use.error", true);
            addSpanEvent(span, "invite.use.error", {
              error:
                inviteError instanceof Error
                  ? inviteError.message
                  : "Unknown error",
            });
            // Don't fail the whole request if invite usage fails
            console.error("Invite use failed:", inviteError);
          }
        }

        addSpanEvent(span, "profile.complete.success");
        console.log("Profile completed successfully", {
          userId: body.userId,
          username: normalizedUsername,
        });

        return NextResponse.json({
          message: "Profile completed successfully",
          username: normalizedUsername,
        });
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error";
        span.setAttribute("error", true);
        span.setAttribute("error.message", errorMessage);

        addSpanEvent(span, "profile.complete.error", {
          error: errorMessage,
        });

        console.error("Complete profile error:", error);
        return NextResponse.json(
          { error: "Failed to complete profile" },
          { status: 500 },
        );
      }
    },
    {
      attributes: {
        component: "user-api",
        operation: "complete-profile",
      },
      kind: "server",
    },
  );
}
