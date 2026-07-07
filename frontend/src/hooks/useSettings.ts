import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AlertSetting {
  key: string;
  value: number;
  label: string;
}

async function fetchSettings(): Promise<AlertSetting[]> {
  const { data } = await api.get<AlertSetting[]>("/api/settings/");
  return data;
}

async function saveSettings(settings: AlertSetting[]): Promise<AlertSetting[]> {
  const { data } = await api.put<AlertSetting[]>("/api/settings/", { settings });
  return data;
}

export function useSettings() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });

  const mutation = useMutation({
    mutationFn: saveSettings,
    onSuccess: (data) => {
      queryClient.setQueryData(["settings"], data);
      // Invalidates alert system query to update UI immediately
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    save: mutation.mutate,
    isSaving: mutation.isPending,
    saveError: mutation.error,
    isSaveSuccess: mutation.isSuccess,
    resetSaveState: mutation.reset,
  };
}
