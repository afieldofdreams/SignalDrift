const BASE_URL = import.meta.env.VITE_API_URL ?? '';

interface ApiResponse<T> {
  data: T;
  ok: true;
}

interface ApiError {
  error: string;
  ok: false;
}

type ApiResult<T> = ApiResponse<T> | ApiError;

export async function apiFetch<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${BASE_URL}${path}`);
    if (!response.ok) {
      return { ok: false, error: `HTTP ${response.status}: ${response.statusText}` };
    }
    const data: T = await response.json();
    return { ok: true, data };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { ok: false, error: message };
  }
}
