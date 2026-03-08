export interface ApiErrorPayload {
  detail?: string;
  message?: string;
}

export class ApiHttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiHttpError";
    this.status = status;
  }
}

export async function fetchApi(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url =
    typeof input === "string"
      ? input
      : input instanceof URL
        ? input.toString()
        : input.url;
  const response = await fetch(input, {
    ...init,
    credentials: init?.credentials ?? "include",
  });

  if (response.status === 401 || response.status === 403) {
    window.dispatchEvent(
      new CustomEvent("kicad-prism-auth-error", {
        detail: { status: response.status, url },
      })
    );
  }

  return response;
}

export async function readApiError(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.detail || payload.message || fallback;
  } catch {
    return fallback;
  }
}

export async function fetchJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
  fallbackError = "Request failed"
): Promise<T> {
  const response = await fetchApi(input, init);
  if (!response.ok) {
    throw new ApiHttpError(response.status, await readApiError(response, fallbackError));
  }
  return (await response.json()) as T;
}
