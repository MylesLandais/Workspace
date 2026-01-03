import { Platform } from '../schema/schema.js';

export type IdentityProfile = {
  id: string;
  name: string;
  bio: string;
  avatarUrl: string;
  aliases: string[];
  sources: SourceLink[];
  contextKeywords: string[];
  imagePool: string[];
  relationships: Relationship[];
};

export type SourceLink = {
  platform: Platform;
  id: string;
  label?: string;
  hidden: boolean;
};

export type Relationship = {
  targetId: string;
  type: string;
  target?: IdentityProfile;
};
