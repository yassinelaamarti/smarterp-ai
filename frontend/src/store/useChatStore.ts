import { create } from "zustand";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatState {
  messages: ChatMessage[];
  error: string | null;
  addMessage: (message: ChatMessage) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

/**
 * Vit en dehors du cycle de vie de ChatWindow : contrairement à un useState
 * dans un hook, cet état n'est PAS réinitialisé quand on quitte /dashboard/chat
 * puis qu'on y revient (le composant est démonté/remonté, mais ce store non).
 */
export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  error: null,
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setError: (error) => set({ error }),
  reset: () => set({ messages: [], error: null }),
}));
