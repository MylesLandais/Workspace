/**
 * Custom schema loader for GraphQL Code Generator
 * Extracts GraphQL schema from Apollo Server typeDefs
 */

import { extract } from "@graphql-tools/extract";

export default function (schemaPath, config) {
  return extract(schemaPath);
}
