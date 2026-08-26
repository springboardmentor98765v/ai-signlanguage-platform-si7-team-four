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
    const storedUsername = localStorage.getItem('username');
    const storedRole = localStorage.getItem('user_role');
    const storedId = localStorage.getItem('user_id');
    if (token && storedUsername && storedId) {
      return {
        user_id: storedId,
        username: storedUsername,
        email: localStorage.getItem('user_email') || '',
        role: storedRole || 'Learner',
      };
    }
    return null;
  });

  const [loading, setLoading] = useState(false);

  const login = async (credentials) => {
    setLoading(true);
    try {
      const data = await apiLogin(credentials);
      const userInfo = data.user;
      if (!userInfo) {
        throw new Error('Login response did not include user details.');
      }

      localStorage.setItem('access_token', data.access_token);
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
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
    localStorage.removeItem('refresh_token');
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
