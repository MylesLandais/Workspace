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


