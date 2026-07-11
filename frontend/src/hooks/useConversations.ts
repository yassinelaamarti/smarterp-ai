import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ConversationSummary {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
}

interface ConversationApiResponse {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

function mapConversation(c: ConversationApiResponse): ConversationSummary {
  return { id: c.id, title: c.title, createdAt: c.created_at, updatedAt: c.updated_at };
}

async function fetchConversations(): Promise<ConversationSummary[]> {
  const { data } = await api.get<ConversationApiResponse[]>("/api/conversations/");
  return data.map(mapConversation);
}

async function createConversationRequest(): Promise<ConversationSummary> {
  const { data } = await api.post<ConversationApiResponse>("/api/conversations/");
  return mapConversation(data);
}

async function deleteConversationRequest(id: number): Promise<void> {
  await api.delete(`/api/conversations/${id}`);
}

export function useConversations() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["conversations"],
    queryFn: fetchConversations,
  });

  const createMutation = useMutation({
    mutationFn: createConversationRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConversationRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  return {
    conversations: query.data ?? [],
    isLoading: query.isLoading,
    createConversation: () => createMutation.mutateAsync(),
    deleteConversation: (id: number) => deleteMutation.mutate(id),
  };
}
