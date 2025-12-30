import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AdminConsole from '../AdminConsole';

describe('AdminConsole', () => {
  it('renders creator list', () => {
    render(<AdminConsole />);
    
    expect(screen.getByText(/Creators/i)).toBeInTheDocument();
  });

  it('displays creator count', () => {
    render(<AdminConsole />);
    
    const countText = screen.getByText(/Creators \(\d+\)/i);
    expect(countText).toBeInTheDocument();
  });

  it('shows creator details when selected', () => {
    render(<AdminConsole />);
    
    // Click on first creator
    const creators = screen.getAllByText(/Sjokz|Brooke Monk/i);
    if (creators.length > 0) {
      fireEvent.click(creators[0]);
      
      // Should show creator details
      expect(screen.getByText(/Eefje Depoortere|Brooke Monk/i)).toBeInTheDocument();
    }
  });

  it('displays enhanced metadata for selected creator', () => {
    render(<AdminConsole />);
    
    const creators = screen.getAllByText(/Sjokz/i);
    if (creators.length > 0) {
      fireEvent.click(creators[0]);
      
      // Check for metadata fields
      waitFor(() => {
        expect(screen.getByText(/Birth Date|Birth Place|Nationality/i)).toBeInTheDocument();
      });
    }
  });

  it('shows handles for selected creator', () => {
    render(<AdminConsole />);
    
    const creators = screen.getAllByText(/Sjokz/i);
    if (creators.length > 0) {
      fireEvent.click(creators[0]);
      
      waitFor(() => {
        expect(screen.getByText(/Handles/i)).toBeInTheDocument();
      });
    }
  });

  it('opens discovery modal when clicking discover button', () => {
    render(<AdminConsole />);
    
    const discoverButton = screen.getByText(/Discover Handles/i);
    fireEvent.click(discoverButton);
    
    expect(screen.getByText(/Discover Handles/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/youtube.com/i)).toBeInTheDocument();
  });

  it('opens add creator modal when clicking add button', () => {
    render(<AdminConsole />);
    
    const addButton = screen.getByText(/Add Creator/i);
    fireEvent.click(addButton);
    
    expect(screen.getByText(/Add Creator/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Display Name/i)).toBeInTheDocument();
  });

  it('filters creators by search query', async () => {
    render(<AdminConsole />);
    
    const searchInput = screen.getByPlaceholderText(/Search creators/i);
    fireEvent.change(searchInput, { target: { value: 'Sjokz' } });
    
    await waitFor(() => {
      // Should filter to show only matching creators
      const creatorItems = screen.getAllByText(/Sjokz/i);
      expect(creatorItems.length).toBeGreaterThan(0);
    });
  });

  it('displays data sources for creators', () => {
    render(<AdminConsole />);
    
    const creators = screen.getAllByText(/Sjokz/i);
    if (creators.length > 0) {
      fireEvent.click(creators[0]);
      
      waitFor(() => {
        const dataSources = screen.getAllByText(/wikipedia|instagram|youtube/i);
        expect(dataSources.length).toBeGreaterThan(0);
      });
    }
  });

  it('shows handle verification status', () => {
    render(<AdminConsole />);
    
    const creators = screen.getAllByText(/Sjokz/i);
    if (creators.length > 0) {
      fireEvent.click(creators[0]);
      
      waitFor(() => {
        const verifiedBadges = screen.getAllByText(/Verified|Unverified/i);
        expect(verifiedBadges.length).toBeGreaterThan(0);
      });
    }
  });
});


