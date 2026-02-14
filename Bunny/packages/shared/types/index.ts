/**
 * Shared type definitions used across client and server
 * These types should be the single source of truth for common data structures
 */

export enum Platform {
  REDDIT = "REDDIT",
  YOUTUBE = "YOUTUBE",
  TWITTER = "TWITTER",
  INSTAGRAM = "INSTAGRAM",
  TIKTOK = "TIKTOK",
  VSCO = "VSCO",
  IMAGEBOARD = "IMAGEBOARD",
}

export enum MediaType {
  VIDEO = "VIDEO",
  IMAGE = "IMAGE",
  TEXT = "TEXT",
}

export enum HandleStatus {
  ACTIVE = "ACTIVE",
  SUSPENDED = "SUSPENDED",
  ABANDONED = "ABANDONED",
}
