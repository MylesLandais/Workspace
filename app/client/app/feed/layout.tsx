import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

export default async function FeedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  try {
    const session = await auth.api.getSession({
      headers: await headers(),
    });

    if (!session) {
      redirect("/");
    }
  } catch (error) {
    console.error("FeedLayout: Auth session check failed:", error);
    // Redirect to index on auth error for safety
    redirect("/");
  }

  return <>{children}</>;
}
