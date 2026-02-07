"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Palette,
  Upload,
  Link,
  Code,
  Check,
  Trash2,
  Download,
} from "lucide-react";

interface Theme {
  id: string;
  name: string;
  description: string;
  css: string;
  isPreset?: boolean;
}

const PRESET_THEMES: Theme[] = [
  {
    id: "default",
    name: "Industrial",
    description: "Default milled graphite theme",
    css: "",
    isPreset: true,
  },
  {
    id: "midnight",
    name: "Midnight Blue",
    description: "Deep blue accents on dark",
    css: `
:root {
  --bg-base: #f8fafc;
  --bg-surface: #ffffff;
  --bg-elevated: #f1f5f9;
  --bg-hover: #e2e8f0;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #64748b;
  --border-default: #e2e8f0;
  --accent-primary: #3b82f6;
  --accent-primary-hover: #2563eb;
  --accent-text: #ffffff;
}
.dark {
  --bg-base: #0f172a;
  --bg-surface: #1e293b;
  --bg-elevated: #334155;
  --bg-hover: #475569;
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --border-default: #334155;
  --accent-primary: #60a5fa;
  --accent-primary-hover: #93c5fd;
  --accent-text: #0f172a;
}`,
    isPreset: true,
  },
  {
    id: "forest",
    name: "Forest",
    description: "Natural green palette",
    css: `
:root {
  --bg-base: #fafaf9;
  --bg-surface: #ffffff;
  --bg-elevated: #f5f5f4;
  --bg-hover: #e7e5e4;
  --text-primary: #1c1917;
  --text-secondary: #44403c;
  --text-muted: #78716c;
  --border-default: #e7e5e4;
  --accent-primary: #16a34a;
  --accent-primary-hover: #15803d;
  --accent-text: #ffffff;
}
.dark {
  --bg-base: #0a0f0d;
  --bg-surface: #14201a;
  --bg-elevated: #1e3028;
  --bg-hover: #2d4038;
  --text-primary: #f5f5f4;
  --text-secondary: #d6d3d1;
  --text-muted: #a8a29e;
  --border-default: #1e3028;
  --accent-primary: #4ade80;
  --accent-primary-hover: #86efac;
  --accent-text: #0a0f0d;
}`,
    isPreset: true,
  },
  {
    id: "amber",
    name: "Amber Terminal",
    description: "Retro amber glow",
    css: `
:root {
  --bg-base: #fefce8;
  --bg-surface: #ffffff;
  --bg-elevated: #fef9c3;
  --bg-hover: #fef08a;
  --text-primary: #451a03;
  --text-secondary: #78350f;
  --text-muted: #a16207;
  --border-default: #fef08a;
  --accent-primary: #d97706;
  --accent-primary-hover: #b45309;
  --accent-text: #ffffff;
}
.dark {
  --bg-base: #0c0a05;
  --bg-surface: #1a1508;
  --bg-elevated: #2d2410;
  --bg-hover: #3d3118;
  --text-primary: #fef3c7;
  --text-secondary: #fcd34d;
  --text-muted: #fbbf24;
  --border-default: #2d2410;
  --accent-primary: #fbbf24;
  --accent-primary-hover: #fcd34d;
  --accent-text: #0c0a05;
}
.dark .font-mono, .dark .font-bold { text-shadow: 0 0 10px rgba(251, 191, 36, 0.2); }`,
    isPreset: true,
  },
  {
    id: "rose",
    name: "Rose Gold",
    description: "Elegant rose accents",
    css: `
:root {
  --bg-base: #fdf2f8;
  --bg-surface: #ffffff;
  --bg-elevated: #fce7f3;
  --bg-hover: #fbcfe8;
  --text-primary: #500724;
  --text-secondary: #831843;
  --text-muted: #9d174d;
  --border-default: #fbcfe8;
  --accent-primary: #e11d48;
  --accent-primary-hover: #be123c;
  --accent-text: #ffffff;
}
.dark {
  --bg-base: #0f0a0c;
  --bg-surface: #1f1418;
  --bg-elevated: #2f1f25;
  --bg-hover: #3f2a33;
  --text-primary: #fdf2f8;
  --text-secondary: #fbcfe8;
  --text-muted: #f9a8d4;
  --border-default: #2f1f25;
  --accent-primary: #fb7185;
  --accent-primary-hover: #fda4af;
  --accent-text: #0f0a0c;
}`,
    isPreset: true,
  },
  {
    id: "cyberpunk",
    name: "Cyberpunk",
    description: "Neon purple and cyan",
    css: `
:root {
  --bg-base: #faf5ff;
  --bg-surface: #ffffff;
  --bg-elevated: #f3e8ff;
  --bg-hover: #e9d5ff;
  --text-primary: #2e1065;
  --text-secondary: #581c87;
  --text-muted: #7e22ce;
  --border-default: #e9d5ff;
  --accent-primary: #7c3aed;
  --accent-primary-hover: #6d28d9;
  --accent-text: #ffffff;
}
.dark {
  --bg-base: #0a0510;
  --bg-surface: #150a20;
  --bg-elevated: #1f1030;
  --bg-hover: #2a1540;
  --text-primary: #f0abfc;
  --text-secondary: #e879f9;
  --text-muted: #c026d3;
  --border-default: #1f1030;
  --accent-primary: #22d3ee;
  --accent-primary-hover: #67e8f9;
  --accent-text: #0a0510;
}
.dark button:not(:disabled):hover { box-shadow: 0 0 20px rgba(34, 211, 238, 0.3); }
.dark .font-mono { text-shadow: 0 0 5px currentColor; }`,
    isPreset: true,
  },
  {
    id: "nord",
    name: "Nord",
    description: "Arctic bluish palette",
    css: `
:root {
  --bg-base: #eceff4;
  --bg-surface: #ffffff;
  --bg-elevated: #e5e9f0;
  --bg-hover: #d8dee9;
  --text-primary: #2e3440;
  --text-secondary: #3b4252;
  --text-muted: #434c5e;
  --border-default: #d8dee9;
  --accent-primary: #5e81ac;
  --accent-primary-hover: #4c6a8f;
  --accent-text: #eceff4;
}
.dark {
  --bg-base: #2e3440;
  --bg-surface: #3b4252;
  --bg-elevated: #434c5e;
  --bg-hover: #4c566a;
  --text-primary: #eceff4;
  --text-secondary: #e5e9f0;
  --text-muted: #d8dee9;
  --border-default: #434c5e;
  --accent-primary: #88c0d0;
  --accent-primary-hover: #8fbcbb;
  --accent-text: #2e3440;
}`,
    isPreset: true,
  },
  {
    id: "dracula",
    name: "Dracula",
    description: "Popular dev theme",
    css: `
:root {
  --bg-base: #f8f8f2;
  --bg-surface: #ffffff;
  --bg-elevated: #f1f1eb;
  --bg-hover: #e8e8e2;
  --text-primary: #282a36;
  --text-secondary: #44475a;
  --text-muted: #6272a4;
  --border-default: #e8e8e2;
  --accent-primary: #bd93f9;
  --accent-primary-hover: #9d79d9;
  --accent-text: #282a36;
}
.dark {
  --bg-base: #282a36;
  --bg-surface: #343746;
  --bg-elevated: #44475a;
  --bg-hover: #4d5066;
  --text-primary: #f8f8f2;
  --text-secondary: #f8f8f2;
  --text-muted: #6272a4;
  --border-default: #44475a;
  --accent-primary: #ff79c6;
  --accent-primary-hover: #ff92d0;
  --accent-text: #282a36;
}
.dark a { color: #8be9fd; }
.dark a:hover { color: #50fa7b; }`,
    isPreset: true,
  },
  {
    id: "solarized",
    name: "Solarized",
    description: "Precision colors",
    css: `
:root {
  --bg-base: #fdf6e3;
  --bg-surface: #eee8d5;
  --bg-elevated: #eee8d5;
  --bg-hover: #e0daca;
  --text-primary: #657b83;
  --text-secondary: #586e75;
  --text-muted: #839496;
  --border-default: #eee8d5;
  --accent-primary: #268bd2;
  --accent-primary-hover: #1a6ba2;
  --accent-text: #fdf6e3;
}
.dark {
  --bg-base: #002b36;
  --bg-surface: #073642;
  --bg-elevated: #073642;
  --bg-hover: #094252;
  --text-primary: #839496;
  --text-secondary: #93a1a1;
  --text-muted: #657b83;
  --border-default: #073642;
  --accent-primary: #2aa198;
  --accent-primary-hover: #35b8ae;
  --accent-text: #002b36;
}`,
    isPreset: true,
  },
  {
    id: "high-contrast",
    name: "High Contrast",
    description: "Maximum accessibility",
    css: `
:root {
  --bg-base: #ffffff;
  --bg-surface: #ffffff;
  --bg-elevated: #f5f5f5;
  --bg-hover: #eeeeee;
  --text-primary: #000000;
  --text-secondary: #1a1a1a;
  --text-muted: #333333;
  --border-default: #000000;
  --accent-primary: #000000;
  --accent-primary-hover: #333333;
  --accent-text: #ffffff;
}
.dark {
  --bg-base: #000000;
  --bg-surface: #0a0a0a;
  --bg-elevated: #1a1a1a;
  --bg-hover: #2a2a2a;
  --text-primary: #ffffff;
  --text-secondary: #f5f5f5;
  --text-muted: #cccccc;
  --border-default: #ffffff;
  --accent-primary: #ffffff;
  --accent-primary-hover: #f5f5f5;
  --accent-text: #000000;
}
.border, [class*="border-"] { border-width: 2px !important; }
*:focus { outline: 3px solid var(--focus-ring) !important; outline-offset: 2px !important; }`,
    isPreset: true,
  },
];

interface ThemeCustomizerProps {
  isOpen: boolean;
  onClose: () => void;
}

const ThemeCustomizer: React.FC<ThemeCustomizerProps> = ({
  isOpen,
  onClose,
}) => {
  const [activeTheme, setActiveTheme] = useState<string>("default");
  const [customCSS, setCustomCSS] = useState<string>("");
  const [cssUrl, setCssUrl] = useState<string>("");
  const [customThemes, setCustomThemes] = useState<Theme[]>([]);
  const [showCSSEditor, setShowCSSEditor] = useState(false);
  const [themeName, setThemeName] = useState("");

  // Load saved themes on mount
  useEffect(() => {
    if (typeof window === "undefined") return;

    const savedThemes = localStorage.getItem("bunny-custom-themes");
    const savedActive = localStorage.getItem("bunny-active-theme");
    const savedCSS = localStorage.getItem("bunny-custom-css");

    if (savedThemes) {
      setCustomThemes(JSON.parse(savedThemes));
    }
    if (savedActive) {
      setActiveTheme(savedActive);
    }
    if (savedCSS) {
      setCustomCSS(savedCSS);
    }
  }, []);

  // Apply theme when active theme changes
  useEffect(() => {
    if (typeof window === "undefined") return;
    applyTheme(activeTheme);
    localStorage.setItem("bunny-active-theme", activeTheme);
  }, [activeTheme, customThemes]);

  const applyTheme = (themeId: string) => {
    if (typeof document === "undefined") return;

    // Remove existing custom style
    const existingStyle = document.getElementById("bunny-custom-theme");
    if (existingStyle) {
      existingStyle.remove();
    }

    // Find theme
    const allThemes = [...PRESET_THEMES, ...customThemes];
    const theme = allThemes.find((t) => t.id === themeId);

    if (theme && theme.css) {
      const styleEl = document.createElement("style");
      styleEl.id = "bunny-custom-theme";
      styleEl.textContent = theme.css;
      document.head.appendChild(styleEl);
    }
  };

  const handleLoadFromURL = async () => {
    if (!cssUrl.trim()) return;

    try {
      const response = await fetch(cssUrl);
      if (!response.ok) throw new Error("Failed to fetch CSS");
      const css = await response.text();
      setCustomCSS(css);
      setShowCSSEditor(true);
    } catch (error) {
      alert(
        "Failed to load CSS from URL. Make sure the URL is accessible and returns valid CSS.",
      );
    }
  };

  const handleSaveCustomTheme = () => {
    if (!themeName.trim() || !customCSS.trim()) return;

    const newTheme: Theme = {
      id: `custom-${Date.now()}`,
      name: themeName,
      description: "Custom theme",
      css: customCSS,
    };

    const updatedThemes = [...customThemes, newTheme];
    setCustomThemes(updatedThemes);
    localStorage.setItem("bunny-custom-themes", JSON.stringify(updatedThemes));
    localStorage.setItem("bunny-custom-css", customCSS);

    setActiveTheme(newTheme.id);
    setThemeName("");
    setShowCSSEditor(false);
  };

  const handleApplyCustomCSS = () => {
    if (typeof document === "undefined") return;

    localStorage.setItem("bunny-custom-css", customCSS);

    // Apply directly
    const existingStyle = document.getElementById("bunny-custom-theme");
    if (existingStyle) {
      existingStyle.remove();
    }

    const styleEl = document.createElement("style");
    styleEl.id = "bunny-custom-theme";
    styleEl.textContent = customCSS;
    document.head.appendChild(styleEl);

    setActiveTheme("custom-live");
  };

  const handleDeleteTheme = (themeId: string) => {
    const updatedThemes = customThemes.filter((t) => t.id !== themeId);
    setCustomThemes(updatedThemes);
    localStorage.setItem("bunny-custom-themes", JSON.stringify(updatedThemes));

    if (activeTheme === themeId) {
      setActiveTheme("default");
    }
  };

  const handleExportTheme = () => {
    const theme = [...PRESET_THEMES, ...customThemes].find(
      (t) => t.id === activeTheme,
    );
    if (!theme) return;

    const blob = new Blob([theme.css], { type: "text/css" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${theme.name.toLowerCase().replace(/\s+/g, "-")}.css`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[85vh] bg-white dark:bg-industrial-925 border border-industrial-200 dark:border-industrial-800 overflow-hidden animate-in fade-in zoom-in-95 duration-300 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-industrial-100 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-900 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-industrial-900 dark:bg-white">
              <Palette className="w-5 h-5 text-white dark:text-industrial-900" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-industrial-900 dark:text-white uppercase tracking-wider font-mono">
                Theme Customizer
              </h2>
              <p className="text-[10px] text-industrial-500 dark:text-industrial-400 font-mono tracking-wider">
                10 presets, custom stylesheets
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-industrial-100 dark:hover:bg-industrial-800 text-industrial-400 hover:text-industrial-900 dark:hover:text-white transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Preset Themes */}
          <div className="mb-6">
            <h3 className="text-[10px] font-medium text-industrial-500 dark:text-industrial-400 uppercase tracking-widest font-mono mb-3">
              Preset Themes
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              {PRESET_THEMES.map((theme) => (
                <button
                  key={theme.id}
                  onClick={() => setActiveTheme(theme.id)}
                  className={`p-3 border text-left transition-all ${
                    activeTheme === theme.id
                      ? "border-industrial-900 dark:border-white bg-industrial-50 dark:bg-industrial-800"
                      : "border-industrial-200 dark:border-industrial-700 hover:border-industrial-400 dark:hover:border-industrial-500"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-industrial-900 dark:text-white text-xs truncate">
                      {theme.name}
                    </span>
                    {activeTheme === theme.id && (
                      <Check className="w-3 h-3 text-industrial-900 dark:text-white shrink-0" />
                    )}
                  </div>
                  <span className="text-[9px] text-industrial-500 dark:text-industrial-400 line-clamp-1">
                    {theme.description}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Custom Themes */}
          {customThemes.length > 0 && (
            <div className="mb-6">
              <h3 className="text-[10px] font-medium text-industrial-500 dark:text-industrial-400 uppercase tracking-widest font-mono mb-3">
                Your Custom Themes
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                {customThemes.map((theme) => (
                  <div
                    key={theme.id}
                    className={`p-3 border text-left transition-all relative group ${
                      activeTheme === theme.id
                        ? "border-industrial-900 dark:border-white bg-industrial-50 dark:bg-industrial-800"
                        : "border-industrial-200 dark:border-industrial-700"
                    }`}
                  >
                    <button
                      onClick={() => setActiveTheme(theme.id)}
                      className="w-full text-left"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-industrial-900 dark:text-white text-xs truncate">
                          {theme.name}
                        </span>
                        {activeTheme === theme.id && (
                          <Check className="w-3 h-3 text-industrial-900 dark:text-white" />
                        )}
                      </div>
                      <span className="text-[9px] text-industrial-500 dark:text-industrial-400">
                        {theme.description}
                      </span>
                    </button>
                    <button
                      onClick={() => handleDeleteTheme(theme.id)}
                      className="absolute top-1 right-1 p-1 opacity-0 group-hover:opacity-100 text-industrial-400 hover:text-red-500 transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Load from URL */}
          <div className="mb-6">
            <h3 className="text-[10px] font-medium text-industrial-500 dark:text-industrial-400 uppercase tracking-widest font-mono mb-3">
              Load from URL
            </h3>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-industrial-400" />
                <input
                  type="url"
                  value={cssUrl}
                  onChange={(e) => setCssUrl(e.target.value)}
                  placeholder="https://example.com/theme.css"
                  className="w-full pl-10 pr-4 py-2 border border-industrial-200 dark:border-industrial-700 bg-white dark:bg-industrial-900 focus:ring-1 focus:ring-industrial-900 dark:focus:ring-white outline-none transition-all text-industrial-900 dark:text-white font-mono text-sm"
                />
              </div>
              <button
                onClick={handleLoadFromURL}
                className="px-4 py-2 bg-industrial-100 dark:bg-industrial-800 text-industrial-600 dark:text-industrial-400 hover:text-industrial-900 dark:hover:text-white transition-all font-mono text-sm uppercase tracking-wider"
              >
                <Upload className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Custom CSS Editor */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[10px] font-medium text-industrial-500 dark:text-industrial-400 uppercase tracking-widest font-mono">
                Custom CSS
              </h3>
              <button
                onClick={() => setShowCSSEditor(!showCSSEditor)}
                className="flex items-center gap-1 text-[10px] text-industrial-500 hover:text-industrial-900 dark:hover:text-white font-mono uppercase tracking-wider transition-all"
              >
                <Code className="w-3 h-3" />
                {showCSSEditor ? "Hide Editor" : "Show Editor"}
              </button>
            </div>

            {showCSSEditor && (
              <div className="space-y-3">
                <textarea
                  value={customCSS}
                  onChange={(e) => setCustomCSS(e.target.value)}
                  placeholder={`/* Custom CSS variables */
:root {
  --bg-base: #your-color;
  --accent-primary: #your-accent;
}
.dark {
  --bg-base: #your-dark-bg;
}`}
                  className="w-full h-48 p-4 border border-industrial-200 dark:border-industrial-700 bg-industrial-50 dark:bg-industrial-900 font-mono text-xs text-industrial-900 dark:text-white focus:ring-1 focus:ring-industrial-900 dark:focus:ring-white outline-none transition-all resize-none"
                />

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={themeName}
                    onChange={(e) => setThemeName(e.target.value)}
                    placeholder="Theme name..."
                    className="flex-1 px-4 py-2 border border-industrial-200 dark:border-industrial-700 bg-white dark:bg-industrial-900 font-mono text-sm text-industrial-900 dark:text-white focus:ring-1 focus:ring-industrial-900 dark:focus:ring-white outline-none transition-all"
                  />
                  <button
                    onClick={handleSaveCustomTheme}
                    disabled={!themeName.trim() || !customCSS.trim()}
                    className="px-4 py-2 bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 font-mono text-sm uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed hover:bg-industrial-800 dark:hover:bg-industrial-100 transition-all"
                  >
                    Save Theme
                  </button>
                  <button
                    onClick={handleApplyCustomCSS}
                    disabled={!customCSS.trim()}
                    className="px-4 py-2 border border-industrial-900 dark:border-white text-industrial-900 dark:text-white font-mono text-sm uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed hover:bg-industrial-50 dark:hover:bg-industrial-800 transition-all"
                  >
                    Apply Live
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Export */}
          {activeTheme !== "default" && (
            <div className="pt-4 border-t border-industrial-100 dark:border-industrial-800">
              <button
                onClick={handleExportTheme}
                className="flex items-center gap-2 text-[10px] text-industrial-500 hover:text-industrial-900 dark:hover:text-white font-mono uppercase tracking-wider transition-all"
              >
                <Download className="w-3 h-3" />
                Export Current Theme as CSS
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-industrial-100 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-900 shrink-0">
          <p className="text-[10px] text-industrial-400 dark:text-industrial-500 font-mono">
            Tip: Use CSS variables like{" "}
            <code className="px-1 bg-industrial-200 dark:bg-industrial-800">
              --bg-base
            </code>
            ,{" "}
            <code className="px-1 bg-industrial-200 dark:bg-industrial-800">
              --accent-primary
            </code>{" "}
            to override theme colors.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ThemeCustomizer;
