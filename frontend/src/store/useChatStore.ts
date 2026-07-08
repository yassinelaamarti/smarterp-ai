import { create } from "zustand";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatState {
  messages: ChatMessage[];
  error: string | null;
  isSending: boolean;
  addMessage: (message: ChatMessage) => void;
  setError: (error: string | null) => void;
  setSending: (isSending: boolean) => void;
  reset: () => void;
}

/**
 * Vit en dehors du cycle de vie des composants : n'importe quel composant
 * qui appelle useChat() (ChatWindow, un bouton de suggestion, etc.) lit et
 * écrit dans le MÊME état partagé. C'est ce qui garantit qu'un seul envoi
 * peut être en cours à la fois, peu importe d'où il est déclenché.
 */
export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  error: null,
  isSending: false,
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setError: (error) => set({ error }),
  setSending: (isSending) => set({ isSending }),
  reset: () => set({ messages: [], error: null, isSending: false }),
}));