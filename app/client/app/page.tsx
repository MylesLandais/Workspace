import { SignIn } from "@/components/auth/SignIn";
import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

export default async function Home() {
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  if (session) {
    redirect("/feed");
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Stealth background effects */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-zinc-500/5 rounded-full blur-[120px]" />
      </div>
      
      <div className="w-full flex flex-col items-center gap-12 relative z-10">
        <div className="flex flex-col items-center space-y-4 text-center">
            <div className="w-16 h-16 bg-white flex items-center justify-center rounded-2xl rotate-3 mb-4">
                <span className="text-black text-4xl font-black">B</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-black tracking-tighter text-white uppercase italic">
                Bunny Project
            </h1>
            <p className="text-zinc-500 max-w-sm text-lg font-medium tracking-tight">
                The future of image distribution. Stealth mode engaged.
            </p>
        </div>

        <SignIn />
        
        <div className="text-zinc-700 text-[10px] font-mono uppercase tracking-[0.2em] mt-8">
            Terminal Access Restricted // Protocol 43-B
        </div>
      </div>
    </main>
  );
}
