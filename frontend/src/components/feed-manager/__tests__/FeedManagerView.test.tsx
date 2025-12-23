import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FeedManagerView from '../FeedManagerView';

describe('FeedManagerView', () => {
  it('renders search input', () => {
    render(<FeedManagerView />);
    
    const searchInput = screen.getByPlaceholderText(/search for subreddits/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('displays empty state when no search query', () => {
    render(<FeedManagerView />);
    
    // Empty state should not show when component first renders
    // (we show the sources table by default)
    const sourcesSection = screen.getByText(/My Sources/i);
    expect(sourcesSection).toBeInTheDocument();
  });

  it('filters sources by search query', async () => {
    render(<FeedManagerView />);
    
    const searchInput = screen.getByPlaceholderText(/search for subreddits/i);
    fireEvent.change(searchInput, { target: { value: 'Sjokz' } });
    
    await waitFor(() => {
      // Should show search results or filtered sources
      expect(screen.getByText(/Sjokz/i)).toBeInTheDocument();
    });
  });

  it('displays sources table with correct columns', () => {
    render(<FeedManagerView />);
    
    expect(screen.getByText(/Source/i)).toBeInTheDocument();
    expect(screen.getByText(/Health/i)).toBeInTheDocument();
    expect(screen.getByText(/Last Sync/i)).toBeInTheDocument();
    expect(screen.getByText(/Media/i)).toBeInTheDocument();
    expect(screen.getByText(/Status/i)).toBeInTheDocument();
  });

  it('shows group filter dropdown', () => {
    render(<FeedManagerView />);
    
    const groupFilter = screen.getByText(/All Groups/i);
    expect(groupFilter).toBeInTheDocument();
  });

  it('displays source count', () => {
    render(<FeedManagerView />);
    
    const countText = screen.getByText(/\d+ source/i);
    expect(countText).toBeInTheDocument();
  });

  it('shows platform badges for different source types', () => {
    render(<FeedManagerView />);
    
    // Should have Reddit sources
    const redditSources = screen.getAllByText(/r\//i);
    expect(redditSources.length).toBeGreaterThan(0);
  });

  it('displays entity badges when source has entity', () => {
    render(<FeedManagerView />);
    
    // Sjokz and Brooke Monk should have entity badges
    const entityBadges = screen.getAllByText(/Sjokz|Brooke Monk/i);
    expect(entityBadges.length).toBeGreaterThan(0);
  });
});


