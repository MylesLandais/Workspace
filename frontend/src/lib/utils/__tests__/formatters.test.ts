import { describe, it, expect } from 'vitest';
import { formatTimeAgo } from '../formatters';

describe('formatters', () => {
  describe('formatTimeAgo', () => {
    it('formats minutes ago correctly', () => {
      const now = new Date();
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
      
      const result = formatTimeAgo(fiveMinutesAgo.toISOString());
      expect(result).toMatch(/5m ago/);
    });

    it('formats hours ago correctly', () => {
      const now = new Date();
      const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);
      
      const result = formatTimeAgo(twoHoursAgo.toISOString());
      expect(result).toMatch(/2h ago/);
    });

    it('formats days ago correctly', () => {
      const now = new Date();
      const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
      
      const result = formatTimeAgo(threeDaysAgo.toISOString());
      expect(result).toMatch(/3d ago/);
    });

    it('handles null timestamp', () => {
      const result = formatTimeAgo(null);
      expect(result).toBe('Never');
    });

    it('handles invalid timestamp', () => {
      const result = formatTimeAgo('invalid-date');
      // Should handle gracefully without throwing
      expect(typeof result).toBe('string');
    });
  });
});


