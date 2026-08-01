import { create } from 'zustand';

/**
 * Zustand Global Auth Store
 * Manages JWT authentication tokens, user session metadata, and login/logout lifecycle.
 */
export const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('pipelineiq_user') || 'null'),
  token: localStorage.getItem('pipelineiq_token') || null,
  isAuthenticated: !!localStorage.getItem('pipelineiq_token'),

  login: (userData, token) => {
    localStorage.setItem('pipelineiq_token', token);
    localStorage.setItem('pipelineiq_user', JSON.stringify(userData));
    set({
      user: userData,
      token,
      isAuthenticated: true,
    });
  },

  logout: () => {
    localStorage.removeItem('pipelineiq_token');
    localStorage.removeItem('pipelineiq_user');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },
}));
