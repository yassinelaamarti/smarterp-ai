import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface KpiHistoryPoint {
  date: string;
  value: number;
}

export function useKpiHistory(kpiId: string | null, period: "week" | "month" | "trimester") {
  return useQuery({
    queryKey: ["kpi-history", kpiId, period],
    queryFn: async (): Promise<KpiHistoryPoint[]> => {
      if (!kpiId) return [];
      const { data } = await api.get(`/api/kpis/${kpiId}/history?period=${period}`);
      return data;
    },
    enabled: !!kpiId,
  });
}
