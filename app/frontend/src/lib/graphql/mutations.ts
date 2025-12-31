import { gql } from '@apollo/client';

export const CREATE_CREATOR = gql`
  mutation CreateCreator($name: String!, $displayName: String!) {
    createCreator(name: $name, displayName: $displayName) {
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

export const ADD_HANDLE = gql`
  mutation AddHandle($creatorId: ID!, $platform: Platform!, $username: String!, $url: String!) {
    addHandle(creatorId: $creatorId, platform: $platform, username: $username, url: $url) {
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
`;

export const VERIFY_HANDLE = gql`
  mutation VerifyHandle($handleId: ID!) {
    verifyHandle(handleId: $handleId) {
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
`;

export const UPDATE_HANDLE_STATUS = gql`
  mutation UpdateHandleStatus($handleId: ID!, $status: HandleStatus!) {
    updateHandleStatus(handleId: $handleId, status: $status) {
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
`;

export const TOGGLE_HANDLE_PAUSE = gql`
  mutation ToggleHandlePause($handleId: ID!) {
    toggleHandlePause(handleId: $handleId) {
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
`;

export const REMOVE_HANDLE = gql`
  mutation RemoveHandle($handleId: ID!) {
    removeHandle(handleId: $handleId)
  }
`;

export const SUBSCRIBE_TO_SOURCE = gql`
  mutation SubscribeToSource($subredditName: String!, $groupId: String) {
    subscribeToSource(subredditName: $subredditName, groupId: $groupId) {
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

export const CREATE_FEED_GROUP = gql`
  mutation CreateFeedGroup($name: String!) {
    createFeedGroup(name: $name) {
      id
      name
      createdAt
    }
  }
`;

// Bunny mutations
export const CREATE_SAVED_BOARD = gql`
  mutation CreateSavedBoard($userId: ID!, $input: SavedBoardInput!) {
    createSavedBoard(userId: $userId, input: $input) {
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

export const UPDATE_SAVED_BOARD = gql`
  mutation UpdateSavedBoard($id: ID!, $input: SavedBoardInput!) {
    updateSavedBoard(id: $id, input: $input) {
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

export const DELETE_SAVED_BOARD = gql`
  mutation DeleteSavedBoard($id: ID!) {
    deleteSavedBoard(id: $id)
  }
`;

export const CREATE_IDENTITY_PROFILE = gql`
  mutation CreateIdentityProfile($userId: ID!, $input: IdentityProfileInput!) {
    createIdentityProfile(userId: $userId, input: $input) {
      id
      name
      bio
      avatarUrl
      aliases
      sources {
        platform
        id
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

export const UPDATE_IDENTITY_PROFILE = gql`
  mutation UpdateIdentityProfile($id: ID!, $input: IdentityProfileInput!) {
    updateIdentityProfile(id: $id, input: $input) {
      id
      name
      bio
      avatarUrl
      aliases
      sources {
        platform
        id
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

export const DELETE_IDENTITY_PROFILE = gql`
  mutation DeleteIdentityProfile($id: ID!) {
    deleteIdentityProfile(id: $id)
  }
`;

export const CREATE_RELATIONSHIP = gql`
  mutation CreateRelationship($profileId: ID!, $input: RelationshipInput!) {
    createRelationship(profileId: $profileId, input: $input) {
      targetId
      type
    }
  }
`;

export const DELETE_RELATIONSHIP = gql`
  mutation DeleteRelationship($profileId: ID!, $targetId: ID!) {
    deleteRelationship(profileId: $profileId, targetId: $targetId)
  }
`;


