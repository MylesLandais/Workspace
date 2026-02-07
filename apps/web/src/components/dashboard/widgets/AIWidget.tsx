"use client";

import React, { useState } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";
import { askGemini } from "@/lib/services/geminiService";

interface AIWidgetProps {
  content: string;
}

const AIWidget: React.FC<AIWidgetProps> = ({ content: initialPrompt }) => {
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "ai"; text: string }>
  >([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setLoading(true);

    try {
      const response = await askGemini(userMessage);
      setMessages((prev) => [...prev, { role: "ai", text: response }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "Error: Could not get response" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-industrial-900">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-industrial-400">
            <Sparkles className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-sm">Ask me anything</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg text-sm ${
                msg.role === "user"
                  ? "bg-matcha-500 text-white"
                  : "bg-industrial-100 dark:bg-industrial-800 text-industrial-900 dark:text-white"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-industrial-100 dark:bg-industrial-800 p-3 rounded-lg">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
          </div>
        )}
      </div>

      <div className="shrink-0 p-3 border-t border-industrial-200 dark:border-industrial-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type your message..."
            className="flex-1 px-3 py-2 bg-industrial-50 dark:bg-industrial-950 border border-industrial-200 dark:border-industrial-700 rounded text-sm text-industrial-900 dark:text-white placeholder:text-industrial-400 focus:outline-none focus:ring-2 focus:ring-matcha-500"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-matcha-600 hover:bg-matcha-700 disabled:bg-industrial-300 disabled:cursor-not-allowed text-white rounded transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIWidget;
