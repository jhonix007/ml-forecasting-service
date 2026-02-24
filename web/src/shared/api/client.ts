import { tokenStorage } from "../auth/storage";

const API_BASE = "/api";

function buildHeaders(custom?: HeadersInit) {
  const headers = new Headers(custom);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = tokenStorage.get();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: buildHeaders(options.headers),
  });

  if (!response.ok) {
    let detail = "Запрос не выполнен";
    try {
      const data = await response.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
