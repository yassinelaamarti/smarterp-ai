import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AlertSourceData {
  kpiLabel: string;
  kpiValue: number;
  kpiUnit?: string;
  model: string;
  domain: string;
  formula: string;
  thresholdInfo: string;
  historyValues?: number[];
  zScore?: number;
  mean?: number;
}

export interface Alert {
  id: string;
  kpiId: string;
  severity: "warning" | "critical";
  message: string;
  isAnomaly: boolean;
  sourceData?: AlertSourceData;
}

interface AlertApiResponse {
  id: string;
  kpi_id: string;
  severity: "warning" | "critical";
  message: string;
  is_anomaly: boolean;
  source_data?: {
    kpi_label: string;
    kpi_value: number;
    kpi_unit?: string;
    model: string;
    domain: string;
    formula: string;
    threshold_info: string;
    history_values?: number[];
    z_score?: number;
    mean?: number;
  };
}

async function fetchAlerts(): Promise<Alert[]> {
  const { data } = await api.get<AlertApiResponse[]>("/api/alerts/");
  return data.map((a) => ({
    id: a.id,
    kpiId: a.kpi_id,
    severity: a.severity,
    message: a.message,
    isAnomaly: a.is_anomaly || false,
    sourceData: a.source_data ? {
      kpiLabel: a.source_data.kpi_label,
      kpiValue: a.source_data.kpi_value,
      kpiUnit: a.source_data.kpi_unit,
      model: a.source_data.model,
      domain: a.source_data.domain,
      formula: a.source_data.formula,
      thresholdInfo: a.source_data.threshold_info,
      historyValues: a.source_data.history_values,
      zScore: a.source_data.z_score,
      mean: a.source_data.mean,
    } : undefined,
  }));
}

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 60_000,
  });
}
