import type {
  CheckHealthResponse,
  ListCompetitionsResponse,
  ListSeasonsResponse,
} from "./generated";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Fetch /api<path> and return its JSON as T; throw ApiError on failure. */
async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`/api${path}`);

  if (!response.ok) {
    const body: { detail?: unknown } = await response.json().catch(() => ({}));
    const message =
      typeof body.detail === "string" ? body.detail : response.statusText;
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export function listCompetitions(): Promise<ListCompetitionsResponse> {
  return getJson<ListCompetitionsResponse>("/competitions");
}

export function listSeasons(code: string): Promise<ListSeasonsResponse> {
  return getJson<ListSeasonsResponse>(
    `/competitions/${encodeURIComponent(code)}/seasons`,
  );
}

/** Return the API's health, e.g. {"status": "ok"}. */
export function checkHealth(): Promise<CheckHealthResponse> {
  return getJson<CheckHealthResponse>("/health");
}
