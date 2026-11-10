import { defineConfig } from "@hey-api/openapi-ts";

// Generates the typed API client from openapi.json (written by
// scripts/export_openapi.py). Run with: npm run gen:api
export default defineConfig({
  input: "openapi.json",
  // Treat this folder as a dependency: regenerated on every run, never edited.
  output: "src/api/generated",
  plugins: [
    "@hey-api/client-fetch", // the HTTP client, bundled into the output
    "@hey-api/typescript", // a type per schema, e.g. CompetitionResponse
    "@hey-api/sdk", // a function per operation, e.g. listCompetitions()
  ],
});
