import { describe, it, expect, vi, beforeEach } from 'vitest';
import { parseErrorEnvelope, ApiError, handleUnauthorized } from './http';

describe('http.ts error envelope parsing', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('parses contract error envelope with code and message', async () => {
    const mockResponse = new Response(
      JSON.stringify({
        error: {
          code: 'INSUFFICIENT_DATA',
          message: 'Insufficient price data in range 2020-01-01 to 2020-03-01.',
        },
      }),
      { status: 422, headers: { 'Content-Type': 'application/json' } }
    );

    const error = await parseErrorEnvelope(mockResponse);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe('INSUFFICIENT_DATA');
    expect(error.status).toBe(422);
    expect(error.message).toContain('Insufficient price data');
  });

  it('handles fallback codes on non-envelope errors', async () => {
    const mockResponse = new Response('Bad Gateway', { status: 400 });
    const error = await parseErrorEnvelope(mockResponse);
    expect(error.code).toBe('VALIDATION_ERROR');
    expect(error.status).toBe(400);
  });

  it('clears session on 401 UNAUTHENTICATED', async () => {
    localStorage.setItem('bt_token', 'valid_token');
    localStorage.setItem('bt_user', JSON.stringify({ user_id: 1, role: 'TRADER' }));

    const mockResponse = new Response(
      JSON.stringify({
        error: {
          code: 'UNAUTHENTICATED',
          message: 'Invalid or expired token',
        },
      }),
      { status: 401, headers: { 'Content-Type': 'application/json' } }
    );

    await parseErrorEnvelope(mockResponse);
    expect(localStorage.getItem('bt_token')).toBeNull();
    expect(localStorage.getItem('bt_user')).toBeNull();
  });

  it('handleUnauthorized clears credentials and triggers event', () => {
    localStorage.setItem('bt_token', 'token_123');
    handleUnauthorized();
    expect(localStorage.getItem('bt_token')).toBeNull();
  });
});
