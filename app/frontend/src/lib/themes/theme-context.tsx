import React, { createContext, useContext, useEffect, useState } from 'react';
import { ThemeId, getTheme, defaultTheme, getAllThemes, Theme } from './theme-config';

interface ThemeContextType {
  theme: Theme;
  themeId: ThemeId;
  setTheme: (themeId: ThemeId) => void;
  availableThemes: Theme[];
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'app-theme';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeId, setThemeIdState] = useState<ThemeId>(() => {
    if (typeof window === 'undefined') {
      return defaultTheme;
    }
    const stored = localStorage.getItem(THEME_STORAGE_KEY) as ThemeId | null;
    return (stored && getTheme(stored) ? stored : defaultTheme) as ThemeId;
  });

  useEffect(() => {
    // Sync with what was set in the inline script
    const stored = localStorage.getItem(THEME_STORAGE_KEY) as ThemeId | null;
    if (stored && getTheme(stored) && stored !== themeId) {
      setThemeIdState(stored);
    }
  }, []);

  useEffect(() => {
    const theme = getTheme(themeId);
    const root = document.documentElement;

    root.setAttribute('data-theme', themeId);

    root.style.setProperty('--theme-bg-primary', theme.colors.background.primary);
    root.style.setProperty('--theme-bg-secondary', theme.colors.background.secondary);
    root.style.setProperty('--theme-border-primary', theme.colors.border.primary);
    root.style.setProperty('--theme-text-primary', theme.colors.text.primary);
    root.style.setProperty('--theme-text-secondary', theme.colors.text.secondary);
    root.style.setProperty('--theme-accent-primary', theme.colors.accent.primary);
    root.style.setProperty('--theme-accent-secondary', theme.colors.accent.secondary);
    root.style.setProperty('--theme-accent-tertiary', theme.colors.accent.tertiary);
    root.style.setProperty('--theme-accent-alert', theme.colors.accent.alert);
    root.style.setProperty('--theme-scrollbar-track', theme.colors.scrollbar.track);
    root.style.setProperty('--theme-scrollbar-thumb', theme.colors.scrollbar.thumb);
    root.style.setProperty('--theme-scrollbar-thumb-hover', theme.colors.scrollbar.thumbHover);

    localStorage.setItem(THEME_STORAGE_KEY, themeId);
  }, [themeId]);

  const setTheme = (newThemeId: ThemeId) => {
    setThemeIdState(newThemeId);
  };

  const value: ThemeContextType = {
    theme: getTheme(themeId),
    themeId,
    setTheme,
    availableThemes: getAllThemes(),
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

