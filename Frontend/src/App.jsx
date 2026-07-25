import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Lessons from './pages/Lessons';
import Practice from './pages/Practice';
import Profile from './pages/Profile';
import InstructorDashboard from './pages/InstructorDashboard';
import AdminDashboard from './pages/AdminDashboard';
import Reports from './pages/Reports';

export default function App() {
  return (
    <Router>
      <nav style={{ display: 'flex', gap: '20px', padding: '16px 40px', background: '#0f172a', color: '#fff', alignItems: 'center', flexWrap: 'wrap' }}>
        <strong style={{ fontSize: '18px', color: '#38bdf8' }}>🤟 Sign Language Platform</strong>
        <Link to="/dashboard" style={{ color: '#fff', textDecoration: 'none' }}>Dashboard</Link>
        <Link to="/lessons" style={{ color: '#fff', textDecoration: 'none' }}>Lessons</Link>
        <Link to="/reports" style={{ color: '#fff', textDecoration: 'none' }}>Reports</Link>
        <Link to="/profile" style={{ color: '#fff', textDecoration: 'none' }}>Profile</Link>
        <Link to="/instructor" style={{ color: '#fff', textDecoration: 'none' }}>Instructor</Link>
        <Link to="/admin" style={{ color: '#fff', textDecoration: 'none' }}>Admin</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/lessons" element={<Lessons />} />
        <Route path="/practice" element={<Practice />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/instructor" element={<InstructorDashboard />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/reports" element={<Reports />} />
      </Routes>
    </Router>
  );
}