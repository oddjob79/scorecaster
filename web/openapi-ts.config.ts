import { defineConfig } from "@hey-api/openapi-ts";

// Generates the API's TypeScript types from openapi.json (written by
// scripts/export_openapi.py). Types only: the fetch code is hand-written
// in src/api/. Run with: npm run gen:api
export default defineConfig({
  input: "openapi.json",
  // Regenerated on every run, never edited.
  output: "src/api/generated",
  plugins: ["@hey-api/typescript"],
});
