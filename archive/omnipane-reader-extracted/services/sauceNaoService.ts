import { SauceResult } from '../types';

// Simulating an API call to SauceNAO
// In production, this would use a proxy or server-side function to hide the API key
export const findSauce = async (imageUrl: string): Promise<SauceResult | null> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Mock logic based on URL for demo purposes
      if (imageUrl.includes('cat')) {
        resolve({
          similarity: 94.2,
          sourceUrl: 'https://pixiv.net/artworks/123456',
          artistName: 'NekoArtist',
          extUrl: 'https://danbooru.donmai.us/posts/123456'
        });
      } else {
        resolve({
          similarity: 88.5,
          sourceUrl: 'https://twitter.com/artist/status/987654',
          artistName: 'DigitalPainterX',
        });
      }
    }, 1500);
  });
};