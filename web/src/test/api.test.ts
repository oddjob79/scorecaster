import { http, HttpResponse } from "msw/http";
import { describe, expect, it } from "vitest";

import { ApiError, checkHealth, listCompetitions, listSeasons } from "@/api/api";
import { server } from "./server";

describe("api", () => {
  it("returns the JSON body on success", async () => {
    const competitions = [
      { code: "E0", name: "Premier League", country: "England", tier: 1 },
    ];
    server.use(http.get("/api/competitions", () => HttpResponse.json(competitions)));
    await expect(listCompetitions()).resolves.toEqual(competitions);
  });

  it("puts the competition code in the seasons path", async () => {
    server.use(
      http.get("/api/competitions/:code/seasons", ({ params }) =>
        HttpResponse.json([{ label: params.code, start_year: 2024, end_year: 2025 }]),
      ),
    );
    await expect(listSeasons("SP1")).resolves.toEqual([
      { label: "SP1", start_year: 2024, end_year: 2025 },
    ]);
  });

  it("throws ApiError with FastAPI's detail on a 404", async () => {
    server.use(
      http.get("/api/competitions/:code/seasons", () =>
        HttpResponse.json({ detail: "No competition with code XX" }, { status: 404 }),
      ),
    );
    await expect(listSeasons("XX")).rejects.toBeInstanceOf(ApiError);
    await expect(listSeasons("XX")).rejects.toMatchObject({
      status: 404,
      message: "No competition with code XX",
    });
  });

  it("falls back to the status text when the error body isn't JSON", async () => {
    server.use(
      http.get("/api/health", () =>
        new HttpResponse("<html>Bad Gateway</html>", { status: 502, statusText: "Bad Gateway" }),
      ),
    );
    await expect(checkHealth()).rejects.toMatchObject({
      status: 502,
      message: "Bad Gateway",
    });
  });
});