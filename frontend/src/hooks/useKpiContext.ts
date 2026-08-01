import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface KpiContextData {
  type: "goal" | "funnel" | "table" | "heatmap" | "donut" | "histogram" | "radar" | "win_loss" | "aging" | "leaderboard" | "unpaid_breakdown" | "none" | string;
  data: any;
}


export function useKpiContext(kpiId: string | null, period: string = "month") {
  return useQuery({
    queryKey: ["kpi-context", kpiId, period],
    queryFn: async (): Promise<KpiContextData> => {
      if (!kpiId) return { type: "none", data: null };
      const response = await api.get(`/api/kpis/${kpiId}/context?period=${period}`);
      return response.data;
    },
    enabled: !!kpiId,
  });
}
