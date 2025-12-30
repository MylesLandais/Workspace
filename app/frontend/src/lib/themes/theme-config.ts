export type ThemeId = 'kanagawa-dragon' | 'default';

export interface ThemeColors {
  background: {
    primary: string;
    secondary: string;
  };
  border: {
    primary: string;
  };
  text: {
    primary: string;
    secondary: string;
  };
  accent: {
    primary: string;
    secondary: string;
    tertiary: string;
    alert: string;
  };
  scrollbar: {
    track: string;
    thumb: string;
    thumbHover: string;
  };
}

export interface Theme {
  id: ThemeId;
  name: string;
  colors: ThemeColors;
}

export const themes: Record<ThemeId, Theme> = {
  'kanagawa-dragon': {
    id: 'kanagawa-dragon',
    name: 'Kanagawa Dragon',
    colors: {
      background: {
        primary: '#181616',
        secondary: '#1F1F1F',
      },
      border: {
        primary: '#2A2A2A',
      },
      text: {
        primary: '#DCD7BA',
        secondary: '#727169',
      },
      accent: {
        primary: '#98BB6C',
        secondary: '#2D4F67',
        tertiary: '#7FB4CA',
        alert: '#E46876',
      },
      scrollbar: {
        track: '#181616',
        thumb: '#2D4F67',
        thumbHover: '#98BB6C',
      },
    },
  },
  default: {
    id: 'default',
    name: 'Default',
    colors: {
      background: {
        primary: '#0a0a0a',
        secondary: '#111827',
      },
      border: {
        primary: '#1f2937',
      },
      text: {
        primary: '#f3f4f6',
        secondary: '#9ca3af',
      },
      accent: {
        primary: '#3b82f6',
        secondary: '#60a5fa',
        tertiary: '#93c5fd',
        alert: '#ef4444',
      },
      scrollbar: {
        track: '#0a0a0a',
        thumb: '#374151',
        thumbHover: '#4b5563',
      },
    },
  },
};

export const defaultTheme: ThemeId = 'kanagawa-dragon';

export function getTheme(themeId: ThemeId): Theme {
  return themes[themeId] || themes[defaultTheme];
}

export function getAllThemes(): Theme[] {
  return Object.values(themes);
}

