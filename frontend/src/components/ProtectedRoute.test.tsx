import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from './ProtectedRoute';

describe('ProtectedRoute component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('redirects unauthenticated users to /login', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/run']}>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route
              path="/run"
              element={
                <ProtectedRoute allowedRoles={['TRADER']}>
                  <div>Trader Run Page</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Trader Run Page')).not.toBeInTheDocument();
  });

  it('allows access to TRADER users for TRADER routes', () => {
    localStorage.setItem('bt_token', 'valid_trader_token');
    localStorage.setItem(
      'bt_user',
      JSON.stringify({ user_id: 1, name: 'Trader Bob', email: 'bob@trader.com', role: 'TRADER' })
    );

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/run']}>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route
              path="/run"
              element={
                <ProtectedRoute allowedRoles={['TRADER']}>
                  <div>Trader Run Page</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Trader Run Page')).toBeInTheDocument();
  });

  it('redirects TRADER trying to access ADMIN routes to /run', () => {
    localStorage.setItem('bt_token', 'valid_trader_token');
    localStorage.setItem(
      'bt_user',
      JSON.stringify({ user_id: 1, name: 'Trader Bob', email: 'bob@trader.com', role: 'TRADER' })
    );

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/admin/instruments']}>
          <Routes>
            <Route path="/run" element={<div>Trader Run Page</div>} />
            <Route
              path="/admin/instruments"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <div>Admin Instruments Page</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Trader Run Page')).toBeInTheDocument();
    expect(screen.queryByText('Admin Instruments Page')).not.toBeInTheDocument();
  });
});
