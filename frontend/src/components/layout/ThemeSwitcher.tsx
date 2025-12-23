import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../../lib/themes/theme-context';

export default function ThemeSwitcher() {
  const { theme, themeId, setTheme, availableThemes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleThemeSelect = (newThemeId: string) => {
    setTheme(newThemeId as any);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2 rounded-lg bg-theme-bg-secondary border border-theme-border-primary hover:bg-theme-bg-primary transition-colors"
      >
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-theme-accent-primary"></div>
          <span className="text-sm text-theme-text-primary">{theme.name}</span>
        </div>
        <svg
          className={`w-4 h-4 text-theme-text-secondary transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-theme-bg-secondary border border-theme-border-primary rounded-lg shadow-lg z-50 overflow-hidden">
          {availableThemes.map((t) => (
            <button
              key={t.id}
              onClick={() => handleThemeSelect(t.id)}
              className={`w-full flex items-center space-x-2 px-4 py-2 text-left hover:bg-theme-bg-primary transition-colors ${
                themeId === t.id ? 'bg-theme-bg-primary' : ''
              }`}
            >
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: t.colors.accent.primary }}
              ></div>
              <span className="text-sm text-theme-text-primary">{t.name}</span>
              {themeId === t.id && (
                <svg
                  className="w-4 h-4 ml-auto text-theme-accent-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

