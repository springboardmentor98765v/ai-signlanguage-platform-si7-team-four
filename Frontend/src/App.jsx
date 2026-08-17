import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';

import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Lessons from './pages/Lessons';
import Practice from './pages/Practice';
import Profile from './pages/Profile';
import Leaderboard from './pages/Leaderboard';
import InstructorDashboard from './pages/InstructorDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ReportsCertificate from './pages/ReportsCertificate';
import AccessibilityTrainerDashboard from './pages/AccessibilityTrainerDashboard';

const ProtectedRoute = ({ children, allowedRoles, userRole, isAuthenticated }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(userRole)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

export default function App() {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('app_theme') || 'light');
  const [notifications, setNotifications] = useState([
    { id: 1, message: '🏆 You earned the "7-Day Streak" badge!', read: false, time: '10m ago' },
    { id: 2, message: '🎉 Certificate generated for Alphabet Mastery!', read: false, time: '1h ago' },
    { id: 3, message: '💡 New practice recommendation: Letter M', read: true, time: '1d ago' },
  ]);
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef(null);

  // Apply dark theme attribute across html & body elements
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        setUser(null);
      }
    }
  }, []);

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
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
    window.location.href = '/login';
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, read: true })));
  };

  const unreadCount = notifications.filter((n) => !n.read).length;
  const userRole = user?.role || 'Learner';
  const isAuthenticated = !!localStorage.getItem('access_token') || !!user;

  return (
    <Router>
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
                <Link to="/practice" className="nav-item">Practice</Link>
                <Link to="/leaderboard" className="nav-item">Leaderboard</Link>
                <Link to="/profile" className="nav-item">Profile</Link>
                <Link to="/reports" className="nav-item">Reports</Link>

                {(userRole === 'Instructor' || userRole === 'Administrator') && (
                  <Link to="/instructor" className="nav-item">Instructor</Link>
                )}

                {(userRole === 'Accessibility Trainer' || userRole === 'Administrator') && (
                  <Link to="/trainer-dashboard" className="nav-item">Trainer</Link>
                )}

                {userRole === 'Administrator' && (
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
                      {notifications.map((n) => (
                        <div key={n.id} className={`notif-item ${!n.read ? 'unread' : ''}`}>
                          <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', margin: 0 }}>{n.message}</p>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-light)' }}>{n.time}</span>
                        </div>
                      ))}
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

        {/* Viewport */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login setUser={setUser} />} />
            <Route path="/register" element={<Register />} />

            <Route path="/dashboard" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Dashboard /></ProtectedRoute>} />
            <Route path="/lessons" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Lessons /></ProtectedRoute>} />
            <Route path="/practice" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Practice /></ProtectedRoute>} />
            <Route path="/leaderboard" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Leaderboard /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Profile /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute isAuthenticated={isAuthenticated}><ReportsCertificate /></ProtectedRoute>} />

            <Route path="/instructor" element={
              <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Instructor', 'Administrator']} userRole={userRole}>
                <InstructorDashboard />
              </ProtectedRoute>
            } />

            <Route path="/trainer-dashboard" element={
              <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Accessibility Trainer', 'Administrator']} userRole={userRole}>
                <AccessibilityTrainerDashboard />
              </ProtectedRoute>
            } />

            <Route path="/admin" element={
              <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Administrator']} userRole={userRole}>
                <AdminDashboard />
              </ProtectedRoute>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}