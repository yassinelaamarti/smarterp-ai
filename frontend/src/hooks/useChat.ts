import { useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useChatStore, ChatMessage } from "@/store/useChatStore";

async function sendChatMessage(message: string, history: ChatMessage[]): Promise<string> {
  const { data } = await api.post<{ reply: string }>("/api/chat/", {
    message,
    history,
  });
  return data.reply;
}

export function useChat() {
  const messages = useChatStore((s) => s.messages);
  const error = useChatStore((s) => s.error);
  const addMessage = useChatStore((s) => s.addMessage);
  const setError = useChatStore((s) => s.setError);

  const mutation = useMutation({
    mutationFn: (message: string) => sendChatMessage(message, messages),
    onMutate: (message: string) => {
      setError(null);
      addMessage({ role: "user", content: message });
    },
    onSuccess: (reply: string) => {
      addMessage({ role: "assistant", content: reply });
    },
    onError: (err: Error) => {
      setError(err.message ?? "Erreur de communication avec l'agent IA");
    },
  });

  const sendMessage = useCallback((message: string) => {
    mutation.mutate(message);
  }, [mutation]);

  return {
    messages,
    sendMessage,
    isSending: mutation.isPending,
    error,
  };
}
