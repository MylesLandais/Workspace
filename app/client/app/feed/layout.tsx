import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

export default function FeedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // COMPLETE BYPASS: Remove all auth checks for development
  return <>{children}</>;
}
