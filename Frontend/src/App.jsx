import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';

import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import Lessons from './pages/Lessons';
import Practice from './pages/Practice';
import Profile from './pages/Profile';
import Leaderboard from './pages/Leaderboard';
import InstructorDashboard from './pages/InstructorDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ReportsCertificate from './pages/ReportsCertificate';
import AccessibilityTrainerDashboard from './pages/AccessibilityTrainerDashboard';
import { useAuth } from './context/AuthContext';
import { getMyNotifications, markNotificationRead } from './services/api';

const ProtectedRoute = ({ children, allowedRoles, userRole, isAuthenticated }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(userRole)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

function AppContent() {
  const { user, role, isAuthenticated, logout, setUser } = useAuth();
  const navigate = useNavigate();

  const [theme, setTheme] = useState(() => localStorage.getItem('app_theme') || 'light');
  const [notifications, setNotifications] = useState([]);
  const [toasts, setToasts] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef(null);
  const seenIdsRef = useRef(new Set());

  const userId = user?.user_id || localStorage.getItem('user_id') || '';

  // Apply dark theme attribute across html & body elements
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  const pushToast = useCallback((notification) => {
    setToasts((prev) => [...prev, notification]);
  }, []);

  useEffect(() => {
    if (toasts.length === 0) return;
    const timer = setTimeout(() => {
      setToasts((prev) => prev.slice(1));
    }, 6000);
    return () => clearTimeout(timer);
  }, [toasts]);

  // Poll the real notifications API for logged-in users; surface new events
  // as an in-app toast at the moment they happen (practice recorded, badge
  // earned, certificate ready, etc.).
  const loadNotifications = useCallback(async () => {
    if (!userId) return;
    try {
      const list = await getMyNotifications(userId);
      setNotifications(list);
      for (const n of list) {
        if (!seenIdsRef.current.has(n.id)) {
          seenIdsRef.current.add(n.id);
          pushToast(n);
        }
      }
    } catch (_) {
      // Keep silent on transient network errors; next poll will retry.
    }
  }, [userId, pushToast]);

  useEffect(() => {
    if (!isAuthenticated || !userId) return;
    loadNotifications();
    const poll = setInterval(loadNotifications, 15000);
    return () => clearInterval(poll);
  }, [isAuthenticated, userId, loadNotifications]);

  // Reset seen-id tracking on logout so a fresh login re-surfaces new events.
  useEffect(() => {
    if (!isAuthenticated) {
      seenIdsRef.current = new Set();
      setNotifications([]);
      setToasts([]);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const markAllAsRead = async () => {
    const unread = notifications.filter((n) => !n.is_read);
    await Promise.allSettled(unread.map((n) => markNotificationRead(n.id)));
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  // Section F: role-based navigation. Instructors never see the Practice link.
  const canPractice = ['Learner', 'Administrator', 'Accessibility Trainer'].includes(role);

  return (
    <div>
      {/* Navigation Bar */}
      <nav className="navbar print-hidden">
        <Link to={isAuthenticated ? "/dashboard" : "/login"} className="brand-logo" aria-label="AI Sign Platform Home">
          ✨ AI Sign Platform
        </Link>

        <div className="nav-links">
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="theme-toggle-btn"
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          >
            {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
          </button>

          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="nav-item">Dashboard</Link>
              <Link to="/lessons" className="nav-item">Lessons</Link>
              {canPractice && <Link to="/practice" className="nav-item">Practice</Link>}
              <Link to="/leaderboard" className="nav-item">Leaderboard</Link>
              <Link to="/profile" className="nav-item">Profile</Link>
              <Link to="/reports" className="nav-item">Reports</Link>

              {(role === 'Instructor' || role === 'Administrator') && (
                <Link to="/instructor" className="nav-item">Instructor</Link>
              )}

              {(role === 'Accessibility Trainer' || role === 'Administrator') && (
                <Link to="/trainer-dashboard" className="nav-item">Trainer</Link>
              )}

              {role === 'Administrator' && (
                <Link to="/admin" className="nav-item">Admin</Link>
              )}

              {/* Notification Bell */}
              <div style={{ position: 'relative' }} ref={dropdownRef}>
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="nav-item"
                  aria-label={`Notifications dropdown, ${unreadCount} unread`}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', position: 'relative', fontSize: '1.1rem' }}
                >
                  🔔
                  {unreadCount > 0 && (
                    <span className="notif-badge">{unreadCount}</span>
                  )}
                </button>

                {/* Dropdown Menu */}
                {showNotifications && (
                  <div className="notif-dropdown">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
                      <strong style={{ fontSize: '0.875rem' }}>Notifications</strong>
                      {unreadCount > 0 && (
                        <button onClick={markAllAsRead} style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600 }}>
                          Mark all read
                        </button>
                      )}
                    </div>
                    {notifications.length === 0 ? (
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', padding: '0.5rem 0' }}>No notifications yet.</p>
                    ) : (
                      notifications.slice(0, 20).map((n) => (
                        <div key={n.id} className={`notif-item ${!n.is_read ? 'unread' : ''}`}>
                          <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', margin: 0 }}>{n.message}</p>
                          {n.created_at && (
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-light)' }}>
                              {new Date(n.created_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              <button onClick={handleLogout} className="btn-logout" aria-label="Sign Out">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-item">Login</Link>
              <Link to="/register" className="nav-item nav-btn-primary">Register</Link>
            </>
          )}
        </div>
      </nav>

      {/* Real-event notification toasts */}
      {toasts.map((toast) => (
        <div key={toast.id} className="toast" role="status">
          <strong>{toast.title}</strong>
          <span>{toast.message}</span>
        </div>
      ))}

      {/* Viewport */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          <Route path="/dashboard" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Dashboard /></ProtectedRoute>} />
          <Route path="/lessons" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Lessons /></ProtectedRoute>} />
          <Route path="/practice" element={
            <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Learner', 'Administrator', 'Accessibility Trainer']} userRole={role}>
              <Practice />
            </ProtectedRoute>
          } />
          <Route path="/leaderboard" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Leaderboard /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Profile /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute isAuthenticated={isAuthenticated}><ReportsCertificate /></ProtectedRoute>} />

          <Route path="/instructor" element={
            <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Instructor', 'Administrator']} userRole={role}>
              <InstructorDashboard />
            </ProtectedRoute>
          } />

          <Route path="/trainer-dashboard" element={
            <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Accessibility Trainer', 'Administrator']} userRole={role}>
              <AccessibilityTrainerDashboard />
            </ProtectedRoute>
          } />

          <Route path="/admin" element={
            <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Administrator']} userRole={role}>
              <AdminDashboard />
            </ProtectedRoute>
          } />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}