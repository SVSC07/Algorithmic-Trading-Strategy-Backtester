import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login as apiLogin, register as apiRegister } from '../api/auth';
import { ApiError } from '../api/http';
import { ArrowRight, ShieldCheck, TrendingUp, Sparkles } from 'lucide-react';

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
    <div className="auth-split-wrapper">
      {/* LEFT COLUMN: Deep atmospheric hero panel with volumetric green light */}
      <div className="auth-hero-pane">
        {/* Signature Volumetric Green & Lime Glow Shafts (replaces blue with vibrant green palette) */}
        <div
          style={{
            position: 'absolute',
            bottom: '-15%',
            right: '5%',
            width: '460px',
            height: '760px',
            background:
              'radial-gradient(ellipse 55% 65% at 50% 60%, rgba(163, 230, 53, 0.28) 0%, rgba(22, 163, 74, 0.16) 45%, transparent 75%)',
            filter: 'blur(75px)',
            transform: 'rotate(-14deg)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '8%',
            right: '18%',
            width: '280px',
            height: '420px',
            background:
              'radial-gradient(ellipse at center, rgba(200, 249, 10, 0.38) 0%, rgba(163, 230, 53, 0.18) 50%, transparent 80%)',
            filter: 'blur(55px)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '8%',
            left: '5%',
            width: '280px',
            height: '280px',
            background: 'radial-gradient(circle, rgba(22, 163, 74, 0.1) 0%, transparent 70%)',
            filter: 'blur(80px)',
            pointerEvents: 'none',
          }}
        />

        {/* Top Header in Hero Pane */}
        <div
          style={{
            position: 'relative',
            zIndex: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                overflow: 'hidden',
                boxShadow: '0 4px 14px rgba(163, 230, 53, 0.35)',
                border: '1.5px solid rgba(163, 230, 53, 0.5)',
                backgroundColor: '#C8F90A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img
                src="/logo.png"
                alt="QuantTest Logo"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>
            <span
              style={{
                fontSize: '22px',
                fontWeight: 700,
                fontFamily: 'var(--font-heading)',
                color: '#FFFFFF',
                letterSpacing: '-0.02em',
              }}
            >
              QuantTest
            </span>
          </div>

          <div
            style={{
              padding: '6px 14px',
              borderRadius: '9999px',
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              backdropFilter: 'blur(10px)',
              fontSize: '12px',
              fontWeight: 500,
              color: 'rgba(255, 255, 255, 0.85)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent-lime)',
              }}
            />
            <span>Institutional Engine</span>
          </div>
        </div>

        {/* Bottom Hero Typography & Strategic Message */}
        <div style={{ position: 'relative', zIndex: 10, maxWidth: '520px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '9999px',
              background: 'rgba(255, 255, 255, 0.08)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              color: '#FFFFFF',
              fontSize: '12px',
              fontWeight: 500,
              marginBottom: '20px',
            }}
          >
            <Sparkles size={13} color="var(--accent-lime)" />
            <span>Algorithmic Trading & Analytics</span>
          </div>

          <h2
            style={{
              fontSize: '42px',
              fontWeight: 700,
              lineHeight: 1.15,
              color: '#FFFFFF',
              letterSpacing: '-0.03em',
              fontFamily: 'var(--font-heading)',
              marginBottom: '16px',
            }}
          >
            Your trading strategies,
            <br />
            always precision tested
          </h2>

          <p
            style={{
              fontSize: '15px',
              lineHeight: 1.65,
              color: 'rgba(255, 255, 255, 0.72)',
              margin: 0,
            }}
          >
            Formulate, validate, and stress-test algorithmic models with tick-accurate historical
            execution rules, zero lookahead bias, and instant metrics calculation.
          </p>
        </div>
      </div>

      {/* RIGHT COLUMN: Clean White Auth Form */}
      <div className="auth-form-pane">
        <div
          className="animate-fade-in"
          style={{
            width: '100%',
            maxWidth: '430px',
          }}
        >
          {/* Logo Mark & Header */}
          <div style={{ marginBottom: '28px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                overflow: 'hidden',
                marginBottom: '20px',
                boxShadow: '0 4px 14px rgba(163, 230, 53, 0.4)',
                border: '1.5px solid rgba(163, 230, 53, 0.5)',
                backgroundColor: '#C8F90A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
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
                fontSize: '32px',
                fontWeight: 700,
                color: 'var(--text-main)',
                letterSpacing: '-0.03em',
                fontFamily: 'var(--font-heading)',
                marginBottom: '8px',
              }}
            >
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </h1>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: 0 }}>
              {mode === 'login'
                ? 'Sign in to access your quantitative trading workspace'
                : 'Register your account to begin backtesting strategies'}
            </p>
          </div>

          {/* Mode Toggle Switch */}
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
                fontSize: '13px',
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
                fontSize: '13px',
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

          {/* Form */}
          <form onSubmit={handleSubmit}>
            {mode === 'register' && (
              <div className="form-group" style={{ marginBottom: '18px' }}>
                <label
                  className="form-label"
                  htmlFor="register-name"
                  style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--text-main)',
                    marginBottom: '6px',
                    display: 'block',
                  }}
                >
                  Full Name
                </label>
                <input
                  id="register-name"
                  type="text"
                  className="form-input"
                  style={{ backgroundColor: 'var(--bg-subtle)', borderColor: 'var(--border)' }}
                  placeholder="e.g. Shourya Vardhan"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="form-group" style={{ marginBottom: '18px' }}>
              <label
                className="form-label"
                htmlFor="auth-email"
                style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--text-main)',
                  marginBottom: '6px',
                  display: 'block',
                }}
              >
                Email Address
              </label>
              <input
                id="auth-email"
                type="email"
                className="form-input"
                style={{ backgroundColor: 'var(--bg-subtle)', borderColor: 'var(--border)' }}
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '22px' }}>
              <label
                className="form-label"
                htmlFor="auth-password"
                style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--text-main)',
                  marginBottom: '6px',
                  display: 'block',
                }}
              >
                Password{' '}
                {mode === 'register' && (
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 400 }}>
                    (min 8 characters)
                  </span>
                )}
              </label>
              <input
                id="auth-password"
                type="password"
                className="form-input"
                style={{ backgroundColor: 'var(--bg-subtle)', borderColor: 'var(--border)' }}
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
              style={{
                width: '100%',
                padding: '13px 20px',
                fontSize: '14px',
                fontWeight: 600,
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--accent-dark)',
                color: '#FFFFFF',
                boxShadow: '0 4px 14px rgba(15, 38, 23, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
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
              marginTop: '32px',
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
                style={{ padding: '7px 14px', fontSize: '12px' }}
                onClick={() => fillDemoAccount('TRADER')}
              >
                <TrendingUp size={12} color="var(--gain)" />
                <span>Trader Demo</span>
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '7px 14px', fontSize: '12px' }}
                onClick={() => fillDemoAccount('ADMIN')}
              >
                <ShieldCheck size={12} color="var(--accent-dark)" />
                <span>Admin Demo</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
