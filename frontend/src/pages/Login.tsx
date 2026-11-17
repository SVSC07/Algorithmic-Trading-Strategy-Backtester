import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login as apiLogin, register as apiRegister } from '../api/auth';
import { ApiError } from '../api/http';
import { ArrowRight, ShieldCheck, TrendingUp } from 'lucide-react';

export const Login: React.FC = () => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { loginUser, logout } = useAuth();
  const navigate = useNavigate();

  // Clear any existing session when landing on login page
  useEffect(() => {
    logout();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === 'login') {
        const res = await apiLogin(email, password);
        loginUser(res.token, res.user);
        if (res.user.role === 'ADMIN') {
          navigate('/admin/instruments');
        } else {
          navigate('/run');
        }
      } else {
        const regRes = await apiRegister(name, email, password);
        // Automatically login the newly registered user
        const authRes = await apiLogin(regRes.email, password);
        loginUser(authRes.token, authRes.user);
        navigate('/run');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Quick Demo fill helpers
  const fillDemoAccount = (role: 'TRADER' | 'ADMIN') => {
    setError(null);
    setMode('login');
    if (role === 'TRADER') {
      setEmail('trader@jss.ac.in');
      setPassword('password123');
    } else {
      setEmail('admin@jss.ac.in');
      setPassword('adminpass123');
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        backgroundColor: '#FFFFFF',
      }}
    >
      <div
        className="card animate-fade-in"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '36px 32px',
          boxShadow: 'var(--shadow-card)',
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              overflow: 'hidden',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px',
              boxShadow: '0 6px 18px rgba(163, 230, 53, 0.4)',
              border: '2px solid rgba(163, 230, 53, 0.5)',
              backgroundColor: '#C8F90A',
            }}
          >
            <img
              src="/logo.png"
              alt="QuantTest Logo"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
          <h1
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: 'var(--text-main)',
              letterSpacing: '-0.02em',
              fontFamily: 'var(--font-heading)',
            }}
          >
            QuantTest
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Algorithmic Trading Strategy Backtesting Engine
          </p>
        </div>

        {/* Tab Toggle */}
        <div
          style={{
            display: 'flex',
            background: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-pill)',
            padding: '4px',
            marginBottom: '24px',
            border: '1px solid var(--border)',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setError(null);
            }}
            style={{
              flex: 1,
              padding: '9px 12px',
              fontSize: '14px',
              fontWeight: 600,
              borderRadius: 'var(--radius-pill)',
              border: 'none',
              background: mode === 'login' ? 'var(--accent-lime)' : 'transparent',
              color: mode === 'login' ? 'var(--text-on-lime)' : 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'all 0.18s ease',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setError(null);
            }}
            style={{
              flex: 1,
              padding: '9px 12px',
              fontSize: '14px',
              fontWeight: 600,
              borderRadius: 'var(--radius-pill)',
              border: 'none',
              background: mode === 'register' ? 'var(--accent-lime)' : 'transparent',
              color: mode === 'register' ? 'var(--text-on-lime)' : 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'all 0.18s ease',
            }}
          >
            Register
          </button>
        </div>

        {error && (
          <div className="alert-error" role="alert">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="alert-success" role="status">
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="form-group">
              <label className="form-label" htmlFor="register-name">
                Full Name
              </label>
              <input
                id="register-name"
                type="text"
                className="form-input"
                placeholder="e.g. Shourya Vardhan"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="auth-email">
              Email Address
            </label>
            <input
              id="auth-email"
              type="email"
              className="form-input"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="auth-password">
              Password {mode === 'register' && <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>(min 8 characters)</span>}
            </label>
            <input
              id="auth-password"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '12px', padding: '12px' }}
            disabled={loading}
          >
            {loading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>{mode === 'login' ? 'Sign In to Workspace' : 'Create Trader Account'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Quick Demo Credentials */}
        <div
          style={{
            marginTop: '28px',
            paddingTop: '20px',
            borderTop: '1px solid var(--border)',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Quick fill demo accounts:
          </div>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '6px 14px', fontSize: '12px' }}
              onClick={() => fillDemoAccount('TRADER')}
            >
              <TrendingUp size={12} color="var(--gain)" />
              <span>Trader Demo</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '6px 14px', fontSize: '12px' }}
              onClick={() => fillDemoAccount('ADMIN')}
            >
              <ShieldCheck size={12} color="var(--accent-dark)" />
              <span>Admin Demo</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
