import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';

import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Lessons from './pages/Lessons';
import Practice from './pages/Practice';
import Profile from './pages/Profile';
import InstructorDashboard from './pages/InstructorDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ReportsCertificate from './pages/ReportsCertificate';

// Helper component for protected routes
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

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
    window.location.href = '/login';
  };

  const userRole = user?.role || 'Learner';
  const isAuthenticated = !!localStorage.getItem('access_token') || !!user;

  return (
    <Router>
      <div>
        {/* Navigation Bar */}
        <nav className="navbar print-hidden">
          <Link to={isAuthenticated ? "/dashboard" : "/login"} className="brand-logo">
            AI Sign Platform
          </Link>
          
          <div className="nav-links">
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="nav-item">Dashboard</Link>
                <Link to="/lessons" className="nav-item">Lessons</Link>
                <Link to="/practice" className="nav-item">Practice</Link>
                <Link to="/profile" className="nav-item">Profile</Link>
                <Link to="/reports" className="nav-item">Reports</Link>

                {/* Only Instructors & Administrators can see Instructor tab */}
                {(userRole === 'Instructor' || userRole === 'Administrator') && (
                  <Link to="/instructor" className="nav-item">Instructor</Link>
                )}

                {/* Only Administrators can see Admin tab */}
                {userRole === 'Administrator' && (
                  <Link to="/admin" className="nav-item">Admin</Link>
                )}

                <button onClick={handleLogout} className="nav-item" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontWeight: '600' }}>
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
            {/* Open /login by default at the beginning */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            
            <Route path="/login" element={<Login setUser={setUser} />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Learner Routes */}
            <Route path="/dashboard" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Dashboard /></ProtectedRoute>} />
            <Route path="/lessons" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Lessons /></ProtectedRoute>} />
            <Route path="/practice" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Practice /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute isAuthenticated={isAuthenticated}><Profile /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute isAuthenticated={isAuthenticated}><ReportsCertificate /></ProtectedRoute>} />

            {/* Restricted Instructor Route */}
            <Route path="/instructor" element={
              <ProtectedRoute isAuthenticated={isAuthenticated} allowedRoles={['Instructor', 'Administrator']} userRole={userRole}>
                <InstructorDashboard />
              </ProtectedRoute>
            } />

            {/* Restricted Admin Route */}
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