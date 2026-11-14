import type { AuthResponse, RegisterResponse } from '../types/api';
import { apiClient, USE_MOCKS } from './http';
import { mockApi } from './mocks';

export async function login(email: string, password: string): Promise<AuthResponse> {
  if (USE_MOCKS) {
    return mockApi.login(email, password);
  }
  return apiClient<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(
  name: string,
  email: string,
  password: string
): Promise<RegisterResponse> {
  if (USE_MOCKS) {
    return mockApi.register(name, email, password);
  }
  return apiClient<RegisterResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });
}
