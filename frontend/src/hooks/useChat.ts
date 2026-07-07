import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

async function sendChatMessage(message: string, history: ChatMessage[]): Promise<string> {
  const { data } = await api.post<{ reply: string }>("/api/chat/", {
    message,
    history,
  });
  return data.reply;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (message: string) => sendChatMessage(message, messages),
    onMutate: (message: string) => {
      setError(null);
      setMessages((prev) => [...prev, { role: "user", content: message }]);
    },
    onSuccess: (reply: string) => {
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
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
