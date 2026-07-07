const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Tokens {
  access_token: string;
  refresh_token: string;
}

export function getTokens(): Tokens | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("tokens");
  return raw ? (JSON.parse(raw) as Tokens) : null;
}

export function setTokens(tokens: Tokens | null) {
  if (tokens) localStorage.setItem("tokens", JSON.stringify(tokens));
  else localStorage.removeItem("tokens");
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function refreshTokens(): Promise<Tokens | null> {
  const tokens = getTokens();
  if (!tokens) return null;
  const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: tokens.refresh_token }),
  });
  if (!response.ok) {
    setTokens(null);
    return null;
  }
  const fresh = (await response.json()) as Tokens;
  setTokens(fresh);
  return fresh;
}

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown } = {},
  retry = true
): Promise<T> {
  const tokens = getTokens();
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(tokens ? { Authorization: `Bearer ${tokens.access_token}` } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 401 && retry && tokens) {
    const fresh = await refreshTokens();
    if (fresh) return api<T>(path, options, false);
    window.location.href = "/login";
    throw new ApiError(401, "Sessão expirada");
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* corpo não-JSON */
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
