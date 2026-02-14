import { CodegenConfig } from "@graphql-codegen/cli"

const config: CodegenConfig = {
  schema: process.env.GRAPHQL_ENDPOINT || "http://localhost:4000/api/graphql",
  documents: ["assets/js/**/*.ts", "assets/js/**/*.tsx"],
  generates: {
    "./assets/js/generated/types.ts": {
      plugins: ["typescript", "typescript-operations"],
      config: {
        skipTypename: false,
        withHooks: false,
        withComponent: false,
        withHOC: false,
      },
    },
  },
  ignoreNoDocuments: true,
}

export default config

