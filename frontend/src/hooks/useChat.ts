import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ConversationDetailResponse {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  messages: { role: "user" | "assistant"; content: string; created_at: string }[];
}

async function fetchConversation(id: number): Promise<ConversationDetailResponse> {
  const { data } = await api.get<ConversationDetailResponse>(`/api/conversations/${id}`);
  return data;
}

async function sendMessageRequest(id: number, message: string): Promise<string> {
  const { data } = await api.post<{ conversation_id: number; reply: string }>(
    `/api/conversations/${id}/messages`,
    { message }
  );
  return data.reply;
}

export function useChat(conversationId: number | null) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => fetchConversation(conversationId as number),
    enabled: conversationId !== null,
  });

  const mutation = useMutation({
    mutationFn: (message: string) => sendMessageRequest(conversationId as number, message),
    onMutate: async (message: string) => {
      // Ajout optimiste du message utilisateur, pour un rendu instantané
      // (la vraie sauvegarde arrive côté backend juste après).
      queryClient.setQueryData<ConversationDetailResponse | undefined>(
        ["conversation", conversationId],
        (old) =>
          old
            ? {
                ...old,
                messages: [
                  ...old.messages,
                  { role: "user", content: message, created_at: new Date().toISOString() },
                ],
              }
            : old
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", conversationId] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] }); // titre/tri dans la sidebar
    },
  });

  const messages: ChatMessage[] =
    query.data?.messages.map((m) => ({ role: m.role, content: m.content })) ?? [];

  const sendMessage = (message: string) => {
    if (mutation.isPending || conversationId === null) return;
    mutation.mutate(message);
  };

  return {
    messages,
    sendMessage,
    isSending: mutation.isPending,
    error: mutation.error ? (mutation.error as Error).message : null,
    conversationTitle: query.data?.title ?? null,
  };
}
