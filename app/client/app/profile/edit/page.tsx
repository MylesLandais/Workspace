"use client";

import { useState, useEffect } from "react";
import { useSession } from "@/lib/auth-client";
import { useUserSources } from "@/lib/hooks/use-user-sources";
import {
  ArrowLeft,
  Loader2,
  User,
  Plus,
  Link as LinkIcon,
  Trash2,
  Settings,
  Rss,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface LinkItem {
  id: string;
  title: string;
  url: string;
}

export default function EditProfilePage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const { activeSources, totalCount } = useUserSources();

  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [location, setLocation] = useState("");
  const [website, setWebsite] = useState("");
  const [company, setCompany] = useState("");
  const [customLink, setCustomLink] = useState("");
  const [links, setLinks] = useState<LinkItem[]>([]);
  const [profilePublic, setProfilePublic] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!isPending && !session) {
      router.push("/auth");
      return;
    }

    if (session?.user) {
      fetch("/api/user/profile")
        .then((res) => res.json())
        .then((data) => {
          if (data.user) {
            setName(data.user.name || "");
            setBio(data.user.bio || "");
            setLocation(data.user.location || "");
            setWebsite(data.user.website || "");
            setCompany(data.user.company || "");
            setLinks(data.user.links ? JSON.parse(data.user.links) : []);
            setProfilePublic(data.user.profilePublic || false);
          }
        })
        .catch((err) => console.error("Failed to load profile:", err));
    }
  }, [session, isPending, router]);

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const handleAddLink = () => {
    setLinks([...links, { id: generateId(), title: "", url: "" }]);
  };

  const handleLinkChange = (
    id: string,
    field: "title" | "url",
    value: string,
  ) => {
    setLinks(
      links.map((link) =>
        link.id === id ? { ...link, [field]: value } : link,
      ),
    );
  };

  const handleRemoveLink = (id: string) => {
    setLinks(links.filter((link) => link.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/user/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          bio,
          location,
          website,
          company,
          links: JSON.stringify(links),
          profilePublic,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Failed to update profile");
        setLoading(false);
        return;
      }

      setSuccess("Profile updated successfully!");
      setLoading(false);

      setTimeout(() => {
        router.push("/dashboard");
      }, 1500);
    } catch (err) {
      console.error("Profile update error:", err);
      setError("An unexpected error occurred");
      setLoading(false);
    }
  };

  const handleCancel = () => {
    router.push("/dashboard");
  };

  if (isPending) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center p-4 relative overflow-hidden">
      <Link
        href="/dashboard"
        className="absolute top-8 left-8 text-zinc-500 hover:text-white transition-colors flex items-center gap-2"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="text-sm">Back to Dashboard</span>
      </Link>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-zinc-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-2xl mt-20 relative z-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
            Edit Profile
          </h1>
          <p className="text-zinc-500 text-sm">
            Update your public profile information
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl space-y-6">
            <div className="flex items-center gap-4 pb-6 border-b border-white/5">
              <div className="w-20 h-20 bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center rounded-full">
                <User className="w-10 h-10 text-zinc-400" />
              </div>
              <div>
                <p className="text-white font-semibold">{session.user.email}</p>
                <p className="text-zinc-500 text-sm">
                  @{session.user.name || "username"}
                </p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
                placeholder="Your name"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Bio
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={4}
                maxLength={500}
                className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm resize-none"
                placeholder="Tell us about yourself..."
              />
              <p className="text-xs text-zinc-600 mt-1 px-1">
                {bio.length}/500 characters
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Company
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
                placeholder="Your company or organization"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
                placeholder="City, Country"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Website
              </label>
              <input
                type="url"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
                placeholder="https://example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Custom Link
              </label>
              <input
                type="url"
                value={customLink}
                onChange={(e) => setCustomLink(e.target.value)}
                className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
                placeholder="https://my-custom-link.com"
              />
            </div>

            <div className="space-y-4">
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Link-Tree Links
              </label>
              <div className="space-y-3">
                {links.map((link, index) => (
                  <div
                    key={link.id}
                    className="flex items-center gap-3 p-3 bg-zinc-900/50 border border-white/5 rounded-xl transition-all"
                  >
                    <LinkIcon className="w-5 h-5 text-zinc-500 flex-shrink-0" />
                    <div className="flex-grow flex gap-3">
                      <input
                        type="text"
                        value={link.title}
                        onChange={(e) =>
                          handleLinkChange(link.id, "title", e.target.value)
                        }
                        className="flex-1 px-3 py-2 bg-transparent text-zinc-200 focus:outline-none placeholder-zinc-500 sm:text-sm"
                        placeholder="Link Title (e.g., Twitter)"
                      />
                      <input
                        type="url"
                        value={link.url}
                        onChange={(e) =>
                          handleLinkChange(link.id, "url", e.target.value)
                        }
                        className="flex-1 px-3 py-2 bg-transparent text-zinc-200 focus:outline-none placeholder-zinc-500 sm:text-sm"
                        placeholder="https://link.com"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveLink(link.id)}
                      className="p-2 text-zinc-500 hover:text-red-500 transition-colors rounded-full"
                      aria-label="Remove link"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={handleAddLink}
                className="w-full py-3 px-4 bg-zinc-800 text-white font-semibold rounded-xl hover:bg-zinc-700 transition-colors flex items-center justify-center gap-2 border border-white/10"
              >
                <Plus className="w-5 h-5" />
                Add Custom Link
              </button>
            </div>

            <div className="pt-4 border-t border-white/5">
              <Link
                href="/sources/manage"
                className="flex items-center justify-between p-4 bg-zinc-900/50 border border-white/5 rounded-xl hover:bg-zinc-800/50 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/5 rounded-full flex items-center justify-center text-zinc-400 group-hover:text-white transition-colors">
                    <Rss className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-zinc-300 group-hover:text-white transition-colors">
                      Manage Content Sources
                    </p>
                    <p className="text-xs text-zinc-500">
                      {activeSources.length} active of {totalCount} total
                      sources
                    </p>
                  </div>
                </div>
                <div className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold uppercase tracking-wider text-zinc-500 group-hover:text-zinc-300 transition-colors">
                  {activeSources.length} Active
                </div>
              </Link>
            </div>

            <div className="pt-4 border-t border-white/5">
              <label className="flex items-center justify-between cursor-pointer group">
                <div>
                  <p className="text-sm font-medium text-zinc-300 group-hover:text-white transition-colors">
                    Make profile public
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">
                    Allow others to view your profile at /u/
                    {session?.user?.name || "username"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setProfilePublic(!profilePublic)}
                  className={`relative w-14 h-7 rounded-full transition-colors ${
                    profilePublic ? "bg-white" : "bg-zinc-700"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-6 h-6 bg-zinc-900 rounded-full transition-transform ${
                      profilePublic ? "translate-x-7" : "translate-x-0"
                    }`}
                  />
                </button>
              </label>
            </div>

            {error && (
              <div className="p-4 bg-red-950/20 border border-red-500/20 rounded-xl">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            {success && (
              <div className="p-4 bg-green-950/20 border border-green-500/20 rounded-xl">
                <p className="text-green-400 text-sm">{success}</p>
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 px-4 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                disabled={loading}
                className="py-3 px-6 bg-zinc-800 text-white font-semibold rounded-xl hover:bg-zinc-700 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>

        <div className="text-zinc-700 text-[10px] font-mono uppercase tracking-[0.2em] text-center mt-8">
          System Nebula // Profile Management
        </div>
      </div>
    </main>
  );
}
