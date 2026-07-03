import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { KPI } from "@/types";

interface KPIApiResponse {
  id: string;
  label: string;
  value: number;
  unit?: string;
  trend?: "up" | "down" | "stable";
  change_percent?: number;
}

async function fetchKpis(): Promise<KPI[]> {
  const { data } = await api.get<KPIApiResponse[]>("/api/kpis/");
  return data.map((kpi) => ({
    id: kpi.id,
    label: kpi.label,
    value: kpi.value,
    unit: kpi.unit,
    trend: kpi.trend,
    changePercent: kpi.change_percent,
  }));
}

export function useKpis() {
  return useQuery({
    queryKey: ["kpis"],
    queryFn: fetchKpis,
    refetchInterval: 60_000, // rafraîchit toutes les 60s, cohérent avec un dashboard "temps réel"
  });
}
