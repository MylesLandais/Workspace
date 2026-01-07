"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, User, MapPin, Building2, Globe, Calendar, Lock } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface PublicProfile {
  username: string;
  name: string;
  bio: string;
  location: string;
  website: string;
  company: string;
  image: string;
  joinDate: string;
}

export default function PublicProfilePage() {
  const params = useParams();
  const username = params.username as string;

  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;

    fetch(`/api/user/${username}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          setError(data.error);
        } else {
          setProfile(data.user);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load profile:", err);
        setError("Failed to load profile");
        setLoading(false);
      });
  }, [username]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-zinc-500 text-sm">Loading profile...</div>
      </main>
    );
  }

  if (error === "This profile is private") {
    return (
      <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4">
        <Link
          href="/"
          className="absolute top-8 left-8 text-zinc-500 hover:text-white transition-colors flex items-center gap-2"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="text-sm">Back</span>
        </Link>

        <div className="max-w-md text-center">
          <div className="w-20 h-20 bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center rounded-full mx-auto mb-6">
            <Lock className="w-10 h-10 text-zinc-600" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-3">Private Profile</h1>
          <p className="text-zinc-500 text-sm">
            This user has chosen to keep their profile private.
          </p>
        </div>
      </main>
    );
  }

  if (error || !profile) {
    return (
      <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4">
        <Link
          href="/"
          className="absolute top-8 left-8 text-zinc-500 hover:text-white transition-colors flex items-center gap-2"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="text-sm">Back</span>
        </Link>

        <div className="max-w-md text-center">
          <h1 className="text-2xl font-bold text-white mb-3">User Not Found</h1>
          <p className="text-zinc-500 text-sm">
            The profile @{username} could not be found.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center p-4 relative overflow-hidden">
      <Link
        href="/"
        className="absolute top-8 left-8 text-zinc-500 hover:text-white transition-colors flex items-center gap-2"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="text-sm">Back</span>
      </Link>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-zinc-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-2xl mt-20 relative z-10">
        <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
          <div className="flex flex-col items-center mb-6">
            <div className="w-32 h-32 bg-gradient-to-tr from-zinc-700 to-zinc-500 rounded-full flex items-center justify-center text-white overflow-hidden mb-4">
              {profile.image ? (
                <img src={profile.image} alt={profile.name} className="w-full h-full object-cover" />
              ) : (
                <User className="w-16 h-16" />
              )}
            </div>
            <h1 className="text-3xl font-bold text-white mb-1">{profile.name}</h1>
            <p className="text-zinc-500 text-sm">@{profile.username}</p>
          </div>

          {profile.bio && (
            <div className="mb-6 pb-6 border-b border-white/5">
              <p className="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap">
                {profile.bio}
              </p>
            </div>
          )}

          <div className="space-y-3">
            {profile.company && (
              <div className="flex items-center gap-3 text-sm">
                <Building2 className="w-4 h-4 text-zinc-500" />
                <span className="text-zinc-300">{profile.company}</span>
              </div>
            )}

            {profile.location && (
              <div className="flex items-center gap-3 text-sm">
                <MapPin className="w-4 h-4 text-zinc-500" />
                <span className="text-zinc-300">{profile.location}</span>
              </div>
            )}

            {profile.website && (
              <div className="flex items-center gap-3 text-sm">
                <Globe className="w-4 h-4 text-zinc-500" />
                <a
                  href={profile.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-300 hover:text-white transition-colors underline"
                >
                  {profile.website}
                </a>
              </div>
            )}

            {profile.joinDate && (
              <div className="flex items-center gap-3 text-sm pt-3 border-t border-white/5">
                <Calendar className="w-4 h-4 text-zinc-500" />
                <span className="text-zinc-500">
                  Joined {new Date(profile.joinDate).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="text-zinc-700 text-[10px] font-mono uppercase tracking-[0.2em] text-center mt-8">
          System Nebula // Public Profile
        </div>
      </div>
    </main>
  );
}
