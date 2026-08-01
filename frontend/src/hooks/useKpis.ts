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
  source_data?: {
    model: string;
    domain: string;
    formula: string;
  };
  sample_size?: number;
  sample_warning_threshold?: number;
  sample_unit_label?: string;
  criticality?: "normal" | "attention" | "critical";
  is_snapshot?: boolean;
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
    sourceData: kpi.source_data ? {
      model: kpi.source_data.model,
      domain: kpi.source_data.domain,
      formula: kpi.source_data.formula,
    } : undefined,
    sampleSize: kpi.sample_size,
    sampleWarningThreshold: kpi.sample_warning_threshold,
    sampleUnitLabel: kpi.sample_unit_label,
    criticality: kpi.criticality ?? "normal",
    isSnapshot: kpi.is_snapshot ?? false,
  }));
}



export function useKpis() {
  return useQuery({
    queryKey: ["kpis"],
    queryFn: fetchKpis,
    refetchInterval: 60_000, // rafraîchit toutes les 60s, cohérent avec un dashboard "temps réel"
  });
}
