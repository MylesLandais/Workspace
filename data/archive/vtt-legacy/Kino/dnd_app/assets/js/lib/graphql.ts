import { GraphQLClient } from 'graphql-request';

const client = new GraphQLClient('/api/graphql');

export interface Race {
  name: string;
  source?: string;
  size?: string;
  speed?: number;
  ability_bonuses?: Record<string, number>;
  subraces?: Subrace[];
}

export interface Subrace {
  name: string;
  source?: string;
  ability_bonuses?: Record<string, number>;
}

export interface Class {
  name: string;
  source?: string;
  hit_die?: number;
  primary_ability?: string;
  subclasses?: Subclass[];
  features?: Feature[];
}

export interface Subclass {
  name: string;
  source?: string;
  short_name?: string;
}

export interface Background {
  name: string;
  source?: string;
  description?: string;
  skill_proficiencies?: string[];
  starting_equipment?: string[];
}

export interface Feature {
  name: string;
  level?: number;
  entries?: any;
}

const RACES_QUERY = `
  query GetRaces($source: String, $showLegacy: Boolean) {
    races(source: $source, showLegacy: $showLegacy) {
      name
      source
      size
      speed
      ability_bonuses
      subraces {
        name
        source
        ability_bonuses
      }
    }
  }
`;

const CLASSES_QUERY = `
  query GetClasses($source: String) {
    classes(source: $source) {
      name
      source
      hit_die
      primary_ability
      subclasses {
        name
        source
        short_name
      }
    }
  }
`;

const BACKGROUNDS_QUERY = `
  query GetBackgrounds($source: String) {
    backgrounds(source: $source) {
      name
      source
      description
      skill_proficiencies
      starting_equipment
    }
  }
`;

const SEARCH_RACES_QUERY = `
  query SearchRaces($query: String!) {
    races {
      name
      source
    }
  }
`;

const SEARCH_CLASSES_QUERY = `
  query SearchClasses($query: String!) {
    classes {
      name
      source
    }
  }
`;

export async function getRaces(source?: string, showLegacy: boolean = false): Promise<Race[]> {
  try {
    const data = await client.request<{ races: Race[] }>(RACES_QUERY, { source, showLegacy });
    return data.races;
  } catch (error) {
    console.error('Failed to fetch races:', error);
    return [];
  }
}

export async function getClasses(source?: string): Promise<Class[]> {
  try {
    const data = await client.request<{ classes: Class[] }>(CLASSES_QUERY, { source });
    return data.classes;
  } catch (error) {
    console.error('Failed to fetch classes:', error);
    return [];
  }
}

export async function getBackgrounds(source?: string): Promise<Background[]> {
  try {
    const data = await client.request<{ backgrounds: Background[] }>(BACKGROUNDS_QUERY, { source });
    return data.backgrounds;
  } catch (error) {
    console.error('Failed to fetch backgrounds:', error);
    return [];
  }
}

export async function searchRaces(query: string): Promise<Race[]> {
  try {
    const data = await client.request<{ races: Race[] }>(SEARCH_RACES_QUERY, { query });
    // Filter client-side since GraphQL doesn't have built-in text search
    const lowerQuery = query.toLowerCase();
    return data.races.filter(race => race.name.toLowerCase().includes(lowerQuery));
  } catch (error) {
    console.error('Failed to search races:', error);
    return [];
  }
}

export async function searchClasses(query: string): Promise<Class[]> {
  try {
    const data = await client.request<{ classes: Class[] }>(SEARCH_CLASSES_QUERY, { query });
    const lowerQuery = query.toLowerCase();
    return data.classes.filter(cls => cls.name.toLowerCase().includes(lowerQuery));
  } catch (error) {
    console.error('Failed to search classes:', error);
    return [];
  }
}

export { client };

