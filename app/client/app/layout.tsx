import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SentryProvider } from "@/lib/providers/SentryProvider";
import { ErrorBoundary } from "@/lib/resilience/error-boundary";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "System Nebula",
  description: "Community pages coming soon",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <SentryProvider>
          <ErrorBoundary>{children}</ErrorBoundary>
        </SentryProvider>
      </body>
    </html>
  );
}
