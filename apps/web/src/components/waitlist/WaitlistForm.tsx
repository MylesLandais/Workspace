"use client";

import { useState } from "react";
import { Mail, AlertCircle, CheckCircle } from "lucide-react";

interface WaitlistFormState {
  loading: boolean;
  success: boolean;
  error: string | null;
  submitted: boolean;
}

export function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [state, setState] = useState<WaitlistFormState>({
    loading: false,
    success: false,
    error: null,
    submitted: false,
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setState({ loading: true, success: false, error: null, submitted: false });

    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, source: "landing" }),
      });

      const data = await response.json();

      if (response.ok) {
        setState({
          loading: false,
          success: true,
          error: null,
          submitted: true,
        });
        setEmail("");
        setName("");
      } else {
        setState({
          loading: false,
          success: false,
          error: data.error || data.message || "Failed to join waitlist",
          submitted: false,
        });
      }
    } catch (error) {
      setState({
        loading: false,
        success: false,
        error: "An error occurred. Please try again.",
        submitted: false,
      });
    }
  };

  return (
    <div className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-1">
            Name (optional)
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-1">
            Email
          </label>
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Mail className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={state.loading || state.submitted}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {state.loading ? "Joining..." : "Join"}
            </button>
          </div>
        </div>

        {state.success && (
          <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-green-800">
              Check your email to confirm your subscription.
            </p>
          </div>
        )}

        {state.error && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-800">{state.error}</p>
          </div>
        )}
      </form>
    </div>
  );
}
