"use client";

import React from "react";
import {
  RedditPostCard,
  RedditGalleryEmbed,
  UnixpornWidget,
} from "@/components/reddit";
import type {
  RedditPost,
  RedditImage,
  RedditComment,
} from "@/lib/types/reddit";

// Mock data matching the API schema
const mockPost: RedditPost = {
  id: "1q1fo2z",
  title: "Should she be my first of year?",
  created_utc: new Date(Date.now() - 3600000 * 5).toISOString(), // 5 hours ago
  score: 43,
  num_comments: 2,
  upvote_ratio: 1.0,
  over_18: false,
  url: "https://www.reddit.com/gallery/1q1fo2z",
  selftext: "",
  permalink:
    "/r/JordynJonesCandy/comments/1q1fo2z/should_she_be_my_first_of_year/",
  subreddit: "JordynJonesCandy",
  author: "LivvysPositionPro",
  is_image: true,
  image_url: "https://i.redd.it/example1.jpg",
};

const mockPostNSFW: RedditPost = {
  ...mockPost,
  id: "1q2abc",
  title: "Exclusive content drop",
  over_18: true,
  score: 127,
  num_comments: 15,
};

const mockTextPost: RedditPost = {
  id: "1q3def",
  title: "Discussion: Best workout leggings for running?",
  created_utc: new Date(Date.now() - 86400000 * 2).toISOString(), // 2 days ago
  score: 89,
  num_comments: 42,
  upvote_ratio: 0.94,
  over_18: false,
  url: "https://www.reddit.com/r/lululemon/comments/1q3def/",
  selftext:
    "I've been trying different leggings for my morning runs but can't seem to find the perfect pair. Looking for something that stays up, doesn't show sweat, and has a pocket for my phone. What are your favorites? I've tried the Align but they slip down during intense cardio...",
  permalink:
    "/r/lululemon/comments/1q3def/discussion_best_workout_leggings_for_running/",
  subreddit: "lululemon",
  author: "FitnessEnthusiast",
  is_image: false,
  image_url: null,
};

const mockImages: RedditImage[] = [
  {
    url: "https://picsum.photos/800/1200?random=1",
    image_path: "cache/reddit/images/img1.jpg",
  },
  {
    url: "https://picsum.photos/800/1000?random=2",
    image_path: "cache/reddit/images/img2.jpg",
  },
  {
    url: "https://picsum.photos/800/1100?random=3",
    image_path: "cache/reddit/images/img3.jpg",
  },
];

const mockComments: RedditComment[] = [
  {
    id: "cmt1",
    body: "Absolutely stunning! Great choice to start the year",
    author: "PhotoEnthusiast",
    score: 12,
    depth: 0,
    is_submitter: false,
    created_utc: new Date(Date.now() - 3600000 * 3).toISOString(),
    link_id: "t3_1q1fo2z",
  },
  {
    id: "cmt2",
    body: "Thanks! Spent a lot of time on this edit.",
    author: "LivvysPositionPro",
    score: 8,
    depth: 1,
    is_submitter: true,
    created_utc: new Date(Date.now() - 3600000 * 2).toISOString(),
    link_id: "t3_1q1fo2z",
  },
  {
    id: "cmt3",
    body: "The lighting in this is incredible. What camera/lens combo did you use?",
    author: "GearHead99",
    score: 5,
    depth: 0,
    is_submitter: false,
    created_utc: new Date(Date.now() - 3600000).toISOString(),
    link_id: "t3_1q1fo2z",
  },
];

export default function RedditEmbedsDemo() {
  return (
    <div className="demo-container">
      <header className="demo-header">
        <h1>Reddit Embed Components</h1>
        <p>Premium embeddable views for Reddit content</p>
      </header>

      <main className="demo-content">
        {/* Section: Live Data from Neo4j */}
        <section className="demo-section">
          <h2>Live Data from Neo4j (r/unixporn)</h2>
          <p className="demo-note">
            This widget fetches real data from the Neo4j database via GraphQL.
            Make sure the server is running and Neo4j has unixporn posts.
          </p>
          <UnixpornWidget limit={6} variant="grid" columns={3} />
        </section>

        {/* Section: Variants */}
        <section className="demo-section">
          <h2>Post Card Variants</h2>
          <div className="demo-grid">
            <div className="demo-item">
              <h3>Expanded (Default)</h3>
              <RedditPostCard
                post={mockPost}
                images={mockImages}
                variant="expanded"
              />
            </div>

            <div className="demo-item">
              <h3>Compact</h3>
              <RedditPostCard
                post={mockPost}
                images={mockImages}
                variant="compact"
              />
            </div>

            <div className="demo-item">
              <h3>Minimal (No Image)</h3>
              <RedditPostCard
                post={mockPost}
                images={mockImages}
                variant="minimal"
              />
            </div>
          </div>
        </section>

        {/* Section: Content Types */}
        <section className="demo-section">
          <h2>Content Types</h2>
          <div className="demo-grid demo-grid--2col">
            <div className="demo-item">
              <h3>Text Post</h3>
              <RedditPostCard post={mockTextPost} variant="expanded" />
            </div>

            <div className="demo-item">
              <h3>NSFW Post (Blurred)</h3>
              <RedditPostCard
                post={mockPostNSFW}
                images={mockImages.slice(0, 1)}
                variant="expanded"
                showNSFWBlur={true}
              />
            </div>
          </div>
        </section>

        {/* Section: Gallery Embed */}
        <section className="demo-section">
          <h2>Gallery Embed with Comments</h2>
          <div className="demo-single">
            <RedditGalleryEmbed
              post={mockPost}
              images={mockImages}
              comments={mockComments}
              showComments={true}
              maxComments={3}
            />
          </div>
        </section>

        {/* Section: API Integration Example */}
        <section className="demo-section demo-section--code">
          <h2>Integration Example</h2>
          <pre className="demo-code">
            {`// Using with the Reddit API hooks
import { useRedditPost, RedditGalleryEmbed } from '@/components/reddit-embeds';

function PostEmbed({ postId }: { postId: string }) {
  const { data, loading, error } = useRedditPost(postId);
  
  if (loading) return <Skeleton />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;
  
  return (
    <RedditGalleryEmbed
      post={data.post}
      images={data.images}
      comments={data.comments}
      showComments
    />
  );
}

// API Endpoints Reference:
// GET /posts              - All posts with filters
// GET /subreddit/{name}   - Posts by subreddit
// GET /post/{id}          - Post details + comments + images
// GET /stats              - Database statistics`}
          </pre>
        </section>
      </main>

      <style jsx>{`
        .demo-container {
          min-height: 100vh;
          background: #050505;
          color: #fafafa;
          font-family:
            -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        .demo-header {
          padding: 48px 24px;
          text-align: center;
          border-bottom: 1px solid #1a1a1a;
          background: linear-gradient(180deg, #0a0a0a 0%, #050505 100%);
        }

        .demo-header h1 {
          margin: 0 0 8px;
          font-size: 32px;
          font-weight: 700;
          background: linear-gradient(135deg, #fff 0%, #888 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .demo-header p {
          margin: 0;
          color: #666;
          font-size: 16px;
        }

        .demo-content {
          max-width: 1200px;
          margin: 0 auto;
          padding: 48px 24px;
        }

        .demo-section {
          margin-bottom: 64px;
        }

        .demo-section h2 {
          margin: 0 0 24px;
          font-size: 20px;
          font-weight: 600;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .demo-note {
          margin: 0 0 24px;
          padding: 12px 16px;
          background: #1a1a1a;
          border-left: 3px solid #ff4500;
          border-radius: 4px;
          color: #aaa;
          font-size: 14px;
        }

        .demo-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 24px;
        }

        .demo-grid--2col {
          grid-template-columns: repeat(2, 1fr);
        }

        .demo-item h3 {
          margin: 0 0 12px;
          font-size: 14px;
          font-weight: 500;
          color: #555;
        }

        .demo-single {
          max-width: 600px;
        }

        .demo-section--code {
          background: #0a0a0a;
          border-radius: 12px;
          padding: 24px;
          border: 1px solid #1a1a1a;
        }

        .demo-code {
          margin: 0;
          padding: 16px;
          background: #111;
          border-radius: 8px;
          font-family: "SF Mono", "Fira Code", monospace;
          font-size: 13px;
          line-height: 1.6;
          color: #aaa;
          overflow-x: auto;
          white-space: pre-wrap;
          word-break: break-word;
        }

        @media (max-width: 900px) {
          .demo-grid {
            grid-template-columns: 1fr;
          }
          .demo-grid--2col {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
