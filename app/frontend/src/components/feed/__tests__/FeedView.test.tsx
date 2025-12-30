import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FeedView from '../FeedView';

// Mock the MediaLightbox component
vi.mock('../MediaLightbox', () => ({
  default: ({ isOpen, media, onClose }: any) => {
    if (!isOpen || !media) return null;
    return (
      <div data-testid="lightbox">
        <div data-testid="lightbox-title">{media.title}</div>
        <button onClick={onClose} data-testid="lightbox-close">Close</button>
      </div>
    );
  },
}));

describe('FeedView', () => {
  it('renders feed items in masonry grid', () => {
    render(<FeedView />);
    
    // Check that feed items are rendered
    const images = screen.getAllByRole('img');
    expect(images.length).toBeGreaterThan(0);
  });

  it('displays platform badges on feed items', () => {
    render(<FeedView />);
    
    // Check for platform indicators (Reddit, VSCO, etc.)
    const platformBadges = screen.getAllByText(/^(r\/|YT|VS|@)/);
    expect(platformBadges.length).toBeGreaterThan(0);
  });

  it('opens lightbox when clicking a feed item', async () => {
    render(<FeedView />);
    
    // Find and click first feed item
    const feedItems = screen.getAllByRole('img');
    const firstItem = feedItems[0].closest('[class*="cursor-pointer"]');
    
    if (firstItem) {
      fireEvent.click(firstItem);
      
      await waitFor(() => {
        expect(screen.getByTestId('lightbox')).toBeInTheDocument();
      });
    }
  });

  it('displays media titles on hover', async () => {
    render(<FeedView />);
    
    const feedItems = screen.getAllByRole('img');
    const firstItem = feedItems[0].closest('[class*="group"]');
    
    if (firstItem) {
      fireEvent.mouseEnter(firstItem);
      
      // Titles should be visible on hover
      await waitFor(() => {
        const titles = screen.getAllByText(/Brooke|Summer|Sample/i);
        expect(titles.length).toBeGreaterThan(0);
      });
    }
  });

  it('shows correct platform for each item', () => {
    render(<FeedView />);
    
    // Check for Reddit items
    const redditBadges = screen.getAllByText('r/');
    expect(redditBadges.length).toBeGreaterThan(0);
    
    // Check for VSCO items
    const vscoBadges = screen.getAllByText('VS');
    expect(vscoBadges.length).toBeGreaterThan(0);
  });
});


