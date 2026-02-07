import Link from "next/link";

export const dynamic = "force-dynamic";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold text-white">404</h1>
        <p className="text-zinc-400">Page not found</p>
        <Link
          href="/"
          className="inline-block px-6 py-3 bg-white text-black rounded-lg hover:bg-zinc-200 transition-colors"
        >
          Go Home
        </Link>
      </div>
    </main>
  );
}
