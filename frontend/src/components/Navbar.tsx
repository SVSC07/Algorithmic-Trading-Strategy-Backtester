import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { USE_MOCKS } from '../api/http';
import { LogOut, Bell } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  const initials = user.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : 'U';

  return (
    <header className="nav-header">
      {/* User profile & greeting */}
      <div className="nav-user">
        <div className="user-avatar" title={user.email}>
          {initials}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', fontFamily: 'var(--font-heading)' }}>
              Hello, {user.name}
            </span>
            <span
              className={`badge ${user.role === 'ADMIN' ? 'badge-dark' : 'badge-lime'}`}
              style={{ fontSize: '11px', padding: '2px 8px' }}
            >
              {user.role}
            </span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {user.email}
          </div>
        </div>
      </div>

      {/* Pill Navigation Tabs */}
      <nav className="nav-links" aria-label="Main Navigation">
        {user.role === 'TRADER' ? (
          <>
            <NavLink
              to="/run"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Run
            </NavLink>
            <NavLink
              to="/strategies"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Strategies
            </NavLink>
            <NavLink
              to="/compare"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Compare
            </NavLink>
          </>
        ) : (
          <NavLink
            to="/admin/instruments"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Instruments
          </NavLink>
        )}
      </nav>

      {/* Actions & Utilities */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div
          className="badge badge-neutral"
          style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
          title={USE_MOCKS ? 'Using Client-Side Fixtures' : 'Connected to Backend at http://localhost:8000'}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: USE_MOCKS ? 'var(--accent-lime)' : '#10B981',
            }}
          />
          {USE_MOCKS ? 'MOCK DATA' : 'API 8000'}
        </div>

        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            position: 'relative',
          }}
          title="Notifications"
        >
          <Bell size={16} />
          <span
            style={{
              position: 'absolute',
              top: '-3px',
              right: '-3px',
              background: 'var(--accent-dark)',
              color: 'var(--accent-lime)',
              fontSize: '10px',
              fontWeight: 700,
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            3
          </span>
        </div>

        <button
          onClick={handleLogout}
          className="btn btn-secondary"
          style={{ padding: '7px 14px', fontSize: '13px' }}
          title="Sign out of current account"
        >
          <LogOut size={14} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};
