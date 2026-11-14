import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';

// Six Views
import { Login } from './pages/Login';
import { Run } from './pages/Run';
import { Strategies } from './pages/Strategies';
import { Results } from './pages/Results';
import { Compare } from './pages/Compare';
import { AdminInstruments } from './pages/AdminInstruments';

const RootRedirect: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role === 'ADMIN') {
    return <Navigate to="/admin/instruments" replace />;
  }
  return <Navigate to="/run" replace />;
};

export const AppContent: React.FC = () => {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-sheet">
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<Login />} />

          {/* Trader Routes */}
          <Route
            path="/run"
            element={
              <ProtectedRoute allowedRoles={['TRADER']}>
                <Run />
              </ProtectedRoute>
            }
          />
          <Route
            path="/strategies"
            element={
              <ProtectedRoute allowedRoles={['TRADER']}>
                <Strategies />
              </ProtectedRoute>
            }
          />
          <Route
            path="/results/:id"
            element={
              <ProtectedRoute allowedRoles={['TRADER']}>
                <Results />
              </ProtectedRoute>
            }
          />
          <Route
            path="/compare"
            element={
              <ProtectedRoute allowedRoles={['TRADER']}>
                <Compare />
              </ProtectedRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin/instruments"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminInstruments />
              </ProtectedRoute>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<RootRedirect />} />
        </Routes>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
