import type { ApiErrorEnvelope } from '../types/api';

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

export const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000';
export const USE_MOCKS = import.meta.env?.VITE_USE_MOCKS === 'true'; // Defaults to false; connects to real backend

/**
 * Dispatches a session expiry event so components / router can react cleanly.
 */
export function handleUnauthorized(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('bt_token');
    localStorage.removeItem('bt_user');
    window.dispatchEvent(new Event('bt_unauthorized'));
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }
}

export async function parseErrorEnvelope(res: Response): Promise<ApiError> {
  const status = res.status;
  let code = 'UNKNOWN_ERROR';
  let message = `Request failed with status ${status}`;

  try {
    const data = (await res.json()) as ApiErrorEnvelope;
    if (data?.error?.code && data?.error?.message) {
      code = data.error.code;
      message = data.error.message;
    }
  } catch {
    // Non-JSON or empty response body
    if (status === 400) code = 'VALIDATION_ERROR';
    else if (status === 401) code = 'UNAUTHENTICATED';
    else if (status === 403) code = 'FORBIDDEN';
    else if (status === 404) code = 'NOT_FOUND';
    else if (status === 409) code = 'CONFLICT';
    else if (status === 422) code = 'INSUFFICIENT_DATA';
  }

  if (status === 401) {
    handleUnauthorized();
  }

  return new ApiError(code, message, status);
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('bt_token') : null;
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Set default JSON Content-Type unless sending FormData
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw await parseErrorEnvelope(response);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}
