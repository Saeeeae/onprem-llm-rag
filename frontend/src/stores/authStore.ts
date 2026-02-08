/**
 * Authentication Store using Zustand
 */
import { create } from 'zustand';
import { apiClient, UserInfo } from '../api/client';

interface AuthState {
  isAuthenticated: boolean;
  user: UserInfo | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  isLoading: true,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.login(username, password);
      const user = await apiClient.getUserInfo();
      set({ isAuthenticated: true, user, isLoading: false });
      return true;
    } catch (err) {
      set({ error: 'Invalid credentials', isLoading: false });
      return false;
    }
  },

  logout: () => {
    apiClient.logout();
    set({ isAuthenticated: false, user: null, error: null });
  },

  checkAuth: async () => {
    const token = apiClient.getToken();
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const user = await apiClient.getUserInfo();
      set({ isAuthenticated: true, user, isLoading: false });
    } catch {
      apiClient.logout();
      set({ isAuthenticated: false, user: null, isLoading: false });
    }
  },
}));
