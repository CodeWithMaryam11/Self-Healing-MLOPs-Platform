import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/useAuthStore';

/**
 * ProtectedRoute Wrapper
 * Intercepts unauthenticated navigation attempts and redirects operators to /login
 */
export const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login interface while preserving intended target path
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};
