import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginUser as apiLogin, registerUser as apiRegister } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user_info');
    if (savedUser) {
      try { return JSON.parse(savedUser); } catch (_) {}
    }
    const token = localStorage.getItem('access_token');
    if (token) {
      return {
        user_id: localStorage.getItem('user_id') || 'usr_78910',
        username: localStorage.getItem('username') || 'Learner User',
        email: 'student@example.com',
        role: localStorage.getItem('user_role') || 'Learner',
      };
    }
    return null;
  });

  const [loading, setLoading] = useState(false);

  const login = async (credentials) => {
    setLoading(true);
    try {
      const data = await apiLogin(credentials);
      const userInfo = data.user || {
        user_id: data.user_id || `usr_${Date.now()}`,
        username: credentials.email.split('@')[0],
        email: credentials.email,
        role: 'Learner',
      };

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_id', userInfo.user_id);
      localStorage.setItem('username', userInfo.username);
      localStorage.setItem('user_role', userInfo.role);
      localStorage.setItem('user_info', JSON.stringify(userInfo));

      setUser(userInfo);
      return userInfo;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    try {
      const data = await apiRegister(userData);
      return data;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_info');
    setUser(null);
  };

  const value = {
    user,
    role: user?.role || 'Guest',
    isAuthenticated: !!user,
    loading,
    login,
    register,
    logout,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
