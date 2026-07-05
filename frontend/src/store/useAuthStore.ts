import { create } from "zustand";
import { api } from "@/lib/api";

interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isInitialized: false,

  login: async (token) => {
    localStorage.setItem("token", token);
    
    // Configurer le header pour les requêtes futures
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;

    try {
      const response = await api.get<User>("/api/auth/me");
      set({
        token,
        user: response.data,
        isAuthenticated: true,
      });
    } catch (error) {
      // Si la récupération de l'utilisateur échoue, on nettoie le token
      localStorage.removeItem("token");
      delete api.defaults.headers.common["Authorization"];
      set({
        token: null,
        user: null,
        isAuthenticated: false,
      });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    delete api.defaults.headers.common["Authorization"];
    set({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  },

  initialize: async () => {
    // Si l'initialisation a déjà été faite, on évite les doubles appels
    if (get().isInitialized) return;

    const token = localStorage.getItem("token");
    if (!token) {
      set({ isInitialized: true });
      return;
    }

    // Configurer le header
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;

    try {
      const response = await api.get<User>("/api/auth/me");
      set({
        token,
        user: response.data,
        isAuthenticated: true,
        isInitialized: true,
      });
    } catch (error) {
      // Token expiré ou invalide
      localStorage.removeItem("token");
      delete api.defaults.headers.common["Authorization"];
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isInitialized: true,
      });
    }
  },
}));
