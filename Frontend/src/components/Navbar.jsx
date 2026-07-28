import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-200/80 shadow-xs transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Platform Title */}
        <Link to="/dashboard" className="flex items-center gap-3 group text-decoration-none">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-blue-500 flex items-center justify-center text-white font-bold text-xl shadow-md shadow-indigo-500/25 group-hover:scale-105 group-hover:rotate-3 transition-all duration-300">
            🤟
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-lg text-slate-900 tracking-tight leading-none">
                SignVerse
              </span>
              <span className="bg-indigo-600 text-white text-[10px] font-black px-1.5 py-0.5 rounded-md uppercase tracking-wider">
                AI
              </span>
            </div>
            <span className="text-[10px] font-bold text-slate-400 tracking-wider uppercase block mt-0.5">
              Sign Language Platform
            </span>
          </div>
        </Link>

        {/* Primary Navigation Links */}
        <nav className="hidden md:flex items-center gap-1.5 font-semibold text-sm">
          {isAuthenticated ? (
            <>
              <Link
                to="/dashboard"
                style={{ textDecoration: 'none' }}
                className={`px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 ${
                  isActive('/dashboard')
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20 font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
              >
                <span>📊</span>
                <span>Dashboard</span>
              </Link>

              <Link
                to="/lessons"
                style={{ textDecoration: 'none' }}
                className={`px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 ${
                  isActive('/lessons')
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20 font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
              >
                <span>📚</span>
                <span>Curriculum</span>
              </Link>

              <Link
                to="/practice"
                style={{ textDecoration: 'none' }}
                className={`px-4 py-2 rounded-xl transition-all flex items-center gap-2 ${
                  isActive('/practice')
                    ? 'bg-gradient-to-r from-indigo-600 to-blue-600 text-white font-bold shadow-lg shadow-indigo-500/30'
                    : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100/80 font-bold'
                }`}
              >
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                </span>
                <span>Practice Studio</span>
              </Link>

              <Link
                to="/reports"
                style={{ textDecoration: 'none' }}
                className={`px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 ${
                  isActive('/reports')
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20 font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
              >
                <span>📜</span>
                <span>Reports & Certificate</span>
              </Link>

              {/* Role-Based Navigation Portals */}
              {(user?.role === 'Instructor' || user?.role === 'Administrator') && (
                <Link
                  to="/instructor"
                  style={{ textDecoration: 'none' }}
                  className={`px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 ${
                    isActive('/instructor')
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20 font-bold'
                      : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100/80 font-semibold'
                  }`}
                >
                  <span>👩‍🏫</span>
                  <span>Instructor</span>
                </Link>
              )}

              {user?.role === 'Administrator' && (
                <Link
                  to="/admin"
                  style={{ textDecoration: 'none' }}
                  className={`px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 ${
                    isActive('/admin')
                      ? 'bg-amber-600 text-white shadow-md shadow-amber-500/20 font-bold'
                      : 'text-amber-800 bg-amber-50 hover:bg-amber-100/80 font-semibold'
                  }`}
                >
                  <span>🛡️</span>
                  <span>Admin</span>
                </Link>
              )}
            </>
          ) : (
            <>
              <Link
                to="/login"
                style={{ textDecoration: 'none' }}
                className="px-4 py-2 text-slate-700 hover:text-slate-900 font-semibold"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                style={{ textDecoration: 'none' }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-md shadow-indigo-500/20 transition-all"
              >
                Create Account
              </Link>
            </>
          )}
        </nav>

        {/* User Badge & Actions */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-3">
            <Link
              to="/profile"
              style={{ textDecoration: 'none' }}
              className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-xl hover:bg-slate-100/80 transition-all border border-transparent hover:border-slate-200"
              title="View Profile"
            >
              <div className="relative">
                <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center font-extrabold text-sm shadow-xs">
                  {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-white rounded-full"></span>
              </div>
              <div className="hidden lg:block text-left">
                <span className="text-xs font-bold text-slate-900 block leading-tight">
                  {user.username}
                </span>
                <span className="text-[10px] text-indigo-600 font-bold block uppercase tracking-wider">
                  {user.role}
                </span>
              </div>
            </Link>

            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all border-0 bg-transparent cursor-pointer flex items-center gap-1.5 text-xs font-bold"
              title="Log Out"
            >
              <span>🚪</span>
              <span className="hidden sm:inline">Logout</span>
            </button>

            {/* Mobile Hamburger Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-slate-600 hover:text-slate-900 bg-slate-100 rounded-xl border-0 cursor-pointer"
            >
              {mobileMenuOpen ? '✕' : '☰'}
            </button>
          </div>
        ) : null}
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-slate-200 p-4 space-y-2 animate-fadeIn">
          <Link
            to="/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-4 py-2.5 rounded-xl text-slate-800 font-bold hover:bg-indigo-50"
          >
            📊 Dashboard
          </Link>
          <Link
            to="/lessons"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-4 py-2.5 rounded-xl text-slate-800 font-bold hover:bg-indigo-50"
          >
            📚 Curriculum
          </Link>
          <Link
            to="/practice"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-bold"
          >
            📷 Practice Studio
          </Link>
          <Link
            to="/reports"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-4 py-2.5 rounded-xl text-slate-800 font-bold hover:bg-indigo-50"
          >
            📜 Reports & Certificate
          </Link>
          <Link
            to="/profile"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-4 py-2.5 rounded-xl text-slate-800 font-bold hover:bg-indigo-50"
          >
            👤 User Profile
          </Link>
        </div>
      )}
    </header>
  );
}
