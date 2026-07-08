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
  const isSending = useChatStore((s) => s.isSending);
  const addMessage = useChatStore((s) => s.addMessage);
  const setError = useChatStore((s) => s.setError);
  const setSending = useChatStore((s) => s.setSending);

  const mutation = useMutation({
    mutationFn: (message: string) => sendChatMessage(message, messages),
    onMutate: (message: string) => {
      setError(null);
      setSending(true);
      addMessage({ role: "user", content: message });
    },
    onSuccess: (reply: string) => {
      addMessage({ role: "assistant", content: reply });
    },
    onError: (err: Error) => {
      setError(err.message ?? "Erreur de communication avec l'agent IA");
    },
    onSettled: () => {
      // Se déclenche dans tous les cas (succès OU erreur) : garantit que
      // isSending repasse à false même si la requête échoue.
      setSending(false);
    },
  });

  const sendMessage = useCallback(
    (message: string) => {
      // Lit l'état le plus à jour du store (pas une valeur figée dans la
      // closure) : bloque tout envoi si un autre composant a déjà une
      // requête en cours, même si ce composant-ci n'en a jamais lancé lui-même.
      if (useChatStore.getState().isSending) return;
      mutation.mutate(message);
    },
    [mutation]
  );

  return {
    messages,
    sendMessage,
    isSending,
    error,
  };
}