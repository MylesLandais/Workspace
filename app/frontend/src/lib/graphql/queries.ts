import { gql } from '@apollo/client';

export const FEED_QUERY = gql`
  query Feed($cursor: String, $limit: Int) {
    feed(cursor: $cursor, limit: $limit) {
      edges {
        node {
          id
          title
          imageUrl
          sourceUrl
          publishDate
          score
          subreddit {
            name
          }
          author {
            username
          }
          platform
          handle {
            name
            handle
          }
          mediaType
          viewCount
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;

export const CREATORS_QUERY = gql`
  query Creators($query: String, $limit: Int) {
    creators(query: $query, limit: $limit) {
      id
      slug
      name
      displayName
      bio
      avatarUrl
      verified
      handles {
        id
        platform
        username
        handle
        url
        verified
        status
        mediaCount
        lastSynced
        health
      }
    }
  }
`;

export const CREATOR_QUERY = gql`
  query Creator($slug: String!) {
    creator(slug: $slug) {
      id
      slug
      name
      displayName
      bio
      avatarUrl
      verified
      handles {
        id
        platform
        username
        handle
        url
        verified
        status
        mediaCount
        lastSynced
        health
      }
    }
  }
`;

export const FEED_GROUPS_QUERY = gql`
  query FeedGroups {
    getFeedGroups {
      id
      name
      createdAt
    }
  }
`;

export const SOURCES_QUERY = gql`
  query Sources($groupId: String) {
    getSources(groupId: $groupId) {
      id
      name
      subredditName
      sourceType
      youtubeHandle
      entityId
      entityName
      group
      tags
      isPaused
      lastSynced
      mediaCount
      health
    }
  }
`;

export const SEARCH_SUBREDDITS_QUERY = gql`
  query SearchSubreddits($query: String!) {
    searchSubreddits(query: $query) {
      name
      displayName
      subscriberCount
      description
      iconUrl
      isSubscribed
    }
  }
`;

// Bunny queries
export const GET_SAVED_BOARDS = gql`
  query GetSavedBoards($userId: ID!) {
    getSavedBoards(userId: $userId) {
      id
      name
      filters {
        persons
        sources
        searchQuery
      }
      createdAt
      userId
    }
  }
`;

export const GET_IDENTITY_PROFILES = gql`
  query GetIdentityProfiles($query: String, $limit: Int) {
    getIdentityProfiles(query: $query, limit: $limit) {
      id
      name
      bio
      avatarUrl
      aliases
      sources {
        platform
        id
        databaseId
        label
        hidden
      }
      contextKeywords
      imagePool
      relationships {
        targetId
        type
      }
    }
  }
`;

export const GET_IDENTITY_PROFILE = gql`
  query GetIdentityProfile($id: ID!) {
    getIdentityProfile(id: $id) {
      id
      name
      bio
      avatarUrl
      aliases
      sources {
        platform
        id
        databaseId
        label
        hidden
      }
      contextKeywords
      imagePool
      relationships {
        targetId
        type
        target {
          id
          name
        }
      }
    }
  }
`;

export const FEED_WITH_FILTERS = gql`
  query FeedWithFilters($cursor: String, $limit: Int, $filters: FeedFilters) {
    feed(cursor: $cursor, limit: $limit, filters: $filters) {
      edges {
        node {
          id
          title
          imageUrl
          sourceUrl
          publishDate
          score
          width
          height
          subreddit {
            name
          }
          author {
            username
          }
          platform
          handle {
            name
            handle
          }
          mediaType
          viewCount
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;


