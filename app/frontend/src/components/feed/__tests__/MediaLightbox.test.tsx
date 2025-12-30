import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import MediaLightbox from '../MediaLightbox';

const mockMedia = {
  id: 'test-1',
  title: 'Test Image',
  sourceUrl: 'https://example.com/image.jpg',
  publishDate: '2025-12-22T10:00:00Z',
  thumbnail: 'https://example.com/thumb.jpg',
  mediaType: 'image' as const,
  platform: 'reddit' as const,
  handle: {
    name: 'testsub',
    handle: 'r/testsub',
    creatorName: 'Test Creator',
  },
  metadata: {
    description: 'Test description',
    tags: ['tag1', 'tag2'],
    location: 'Test Location',
  },
};

describe('MediaLightbox', () => {
  it('renders when open with media', () => {
    render(
      <MediaLightbox
        media={mockMedia}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Test Image')).toBeInTheDocument();
    expect(screen.getByText('r/testsub')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <MediaLightbox
        media={mockMedia}
        isOpen={false}
        onClose={vi.fn()}
      />
    );

    expect(screen.queryByText('Test Image')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(
      <MediaLightbox
        media={mockMedia}
        isOpen={true}
        onClose={onClose}
      />
    );

    const closeButton = screen.getByLabelText('Close');
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('displays metadata correctly', () => {
    render(
      <MediaLightbox
        media={mockMedia}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Test description')).toBeInTheDocument();
    expect(screen.getByText('Test Location')).toBeInTheDocument();
    expect(screen.getByText('#tag1')).toBeInTheDocument();
    expect(screen.getByText('#tag2')).toBeInTheDocument();
  });

  it('shows platform badge', () => {
    render(
      <MediaLightbox
        media={mockMedia}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Reddit')).toBeInTheDocument();
  });

  it('displays creator name when available', () => {
    render(
      <MediaLightbox
        media={mockMedia}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText(/Test Creator/)).toBeInTheDocument();
  });

  it('handles keyboard navigation', () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const onClose = vi.fn();

    render(
      <MediaLightbox
        media={mockMedia}
        isOpen={true}
        onClose={onClose}
        onNext={onNext}
        onPrevious={onPrevious}
        hasNext={true}
        hasPrevious={true}
      />
    );

    // Test Escape key
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);

    // Test Arrow Right
    fireEvent.keyDown(document, { key: 'ArrowRight' });
    expect(onNext).toHaveBeenCalledTimes(1);

    // Test Arrow Left
    fireEvent.keyDown(document, { key: 'ArrowLeft' });
    expect(onPrevious).toHaveBeenCalledTimes(1);
  });

  it('renders video player for video media', () => {
    const videoMedia = {
      ...mockMedia,
      mediaType: 'video' as const,
      duration: 120,
    };

    render(
      <MediaLightbox
        media={videoMedia}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    const video = screen.getByRole('video');
    expect(video).toBeInTheDocument();
  });
});


