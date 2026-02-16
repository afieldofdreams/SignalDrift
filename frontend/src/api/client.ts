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

export async function apiPost<T>(path: string, body: unknown): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      const detail = data?.detail ?? `HTTP ${response.status}: ${response.statusText}`;
      return { ok: false, error: detail };
    }
    const data: T = await response.json();
    return { ok: true, data };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { ok: false, error: message };
  }
}

export async function apiDelete<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${BASE_URL}${path}`, { method: 'DELETE' });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail = body?.detail ?? `HTTP ${response.status}: ${response.statusText}`;
      return { ok: false, error: detail };
    }
    const data: T = await response.json();
    return { ok: true, data };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { ok: false, error: message };
  }
}

export async function apiUpload<T>(path: string, file: File): Promise<ApiResult<T>> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail = body?.detail ?? `HTTP ${response.status}: ${response.statusText}`;
      return { ok: false, error: detail };
    }
    const data: T = await response.json();
    return { ok: true, data };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { ok: false, error: message };
  }
}
