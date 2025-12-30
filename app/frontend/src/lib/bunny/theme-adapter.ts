import { Theme as BunnyTheme } from './types';
import { ThemeId } from '../themes/theme-config';

/**
 * Maps Bunny theme names to the unified theme system
 */
export function mapBunnyThemeToThemeId(bunnyTheme: BunnyTheme): ThemeId {
  switch (bunnyTheme) {
    case 'kanagawa':
      return 'kanagawa-dragon';
    case 'default':
      return 'default';
    default:
      return 'kanagawa-dragon';
  }
}

/**
 * Maps unified theme IDs to Bunny theme names
 */
export function mapThemeIdToBunnyTheme(themeId: ThemeId): BunnyTheme {
  switch (themeId) {
    case 'kanagawa-dragon':
      return 'kanagawa';
    case 'default':
      return 'default';
    default:
      return 'kanagawa';
  }
}





